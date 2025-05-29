import uuid
from typing import Annotated, Any, Literal, Sequence, TypedDict

from langchain_core.messages import AnyMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph
from langgraph.graph.message import Messages, add_messages
from langgraph.prebuilt import ToolNode

from .chatbot import AIMessage, BaseMessage, Chatbot


def add_messages_with_log(msg1: Messages, msg2: Messages):
    for msg in msg1:
        if isinstance(msg, BaseMessage):
            msg.pretty_print()
    return add_messages(msg1, msg2)


class State(TypedDict):
    messages: Annotated[Sequence[AnyMessage], add_messages_with_log]


class Workflow:
    state: State = State(messages=[])
    memory = MemorySaver()
    config: RunnableConfig
    tools: Sequence[BaseTool]
    chatbot: Chatbot

    def __init__(self, chatbot: Chatbot, tools: Sequence[BaseTool]):
        self.chatbot = chatbot
        self.tools = tools
        thread_id = uuid.uuid4()
        self.config = {"configurable": {"thread_id": thread_id}}

        workflow = StateGraph(State)
        workflow.add_node("think", self.__call_chatbot)
        workflow.add_edge("__start__", "think")
        workflow.add_node("tools", ToolNode(self.tools))

        workflow.add_conditional_edges("think", self.__route_model_output)
        workflow.add_edge("tools", "think")
        workflow.add_edge("think", "__end__")
        self.app = workflow.compile(checkpointer=self.memory)

    def __call_chatbot(self, state: State):
        messages = state["messages"]
        response = self.chatbot.invoke(messages)
        print("r", response)
        return {"messages": [*messages, response]}

    def __route_model_output(self, state: State) -> Literal["__end__", "tools"]:
        last_message = state["messages"][-1]
        if not isinstance(last_message, AIMessage):
            raise ValueError(f"Expected AIMessage in output edges, but got {type(last_message).__name__}")

        if not last_message.tool_calls:
            return "__end__"
        return "tools"

    def run(self, message: dict[str, str]) -> dict[str, Any] | Any:

        expression = message["expression"]
        msg = HumanMessage(content=expression)
        return self.app.invoke({"messages": [msg]}, self.config)
