import uuid
from typing import Annotated, Any, Literal, Sequence, TypedDict

from langchain_core.messages import AnyMessage, HumanMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph
from langgraph.graph.message import Messages, add_messages
from langgraph.prebuilt import ToolNode

from .chatbot import AIMessage, BaseMessage, Chatbot


def add_messages_with_log(msg1: Messages, msg2: Messages):
    return add_messages(msg1, msg2)


class State(TypedDict):
    messages: Annotated[Sequence[AnyMessage], add_messages_with_log]
    reasoning: Annotated[Sequence[str], lambda x, y: x + y]


class Workflow:
    state: State = State(messages=[], reasoning=[])
    memory = MemorySaver()
    config: RunnableConfig
    tools: Sequence[BaseTool]
    chatbot: Chatbot

    def __init__(self, chatbot: Chatbot, tools: Sequence[BaseTool]):
        self.chatbot = chatbot
        self.tools = tools

        workflow = StateGraph(State)
        workflow.add_node("agent", self.__call_chatbot)
        workflow.add_edge("__start__", "agent")
        workflow.add_node("tools", ToolNode(self.tools))

        workflow.add_conditional_edges("agent", self.__route_model_output)
        workflow.add_edge("tools", "agent")
        workflow.add_edge("agent", "__end__")
        self.app = workflow.compile(checkpointer=self.memory)

        # self.app = workflow.compile()

    def __call_chatbot(self, state: State):
        messages = state["messages"]
        response = self.chatbot.invoke(messages)
        response.pretty_print()
        return {"messages": [*messages, response], "reasoning": state["reasoning"]}

    def __call_reasoning(self, state: State):
        messages = state["messages"]
        reasoning_msg = self.chatbot.invoke_reasoning(messages)
        print("____________REASONING_____________")
        reasoning_msg.pretty_print()
        return {"messages": messages, "reasoning": [reasoning_msg.content]}

    def __route_model_output(self, state: State) -> Literal["__end__", "tools", "agent"]:
        last_message = state["messages"][-1]
        if not isinstance(last_message, AIMessage):
            raise ValueError(f"Expected AIMessage in output edges, but got {type(last_message).__name__}")

        if last_message.content[:5] == "error":
            return "agent"

        if not last_message.tool_calls:
            return "__end__"
        return "tools"

    def run(self, message: dict[str, str]) -> dict[str, Any] | Any:

        expression = message["expression"]
        id = message["id"]
        self.config = {"configurable": {"thread_id": id}}
        msg = HumanMessage(content=expression)
        msg.pretty_print()
        return self.app.invoke({"messages": [msg]}, self.config)

    # return self.app.invoke({"messages": [msg], "reasoning": []})
