from dataclasses import field
from ssl import ALERT_DESCRIPTION_UNEXPECTED_MESSAGE
from typing import Annotated, Any, Literal, Sequence, TypedDict
from uuid import UUID, uuid4

from langchain_core.messages import AnyMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseToolkit
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from .chatbot import AIMessage, Chatbot
from .tools import AnalyticsTool, BaseTool, DataPlacementOptimizerTool, SimilarIntentRetriever


class State(TypedDict):
    messages: Annotated[Sequence[AnyMessage], add_messages]


class Workflow:
    state: State = State(messages=[])
    memory = MemorySaver()
    config: RunnableConfig
    tools: Sequence[BaseTool]
    chatbot: Chatbot

    def __init__(self, chatbot: Chatbot, tools: Sequence[BaseTool]):
        self.chatbot = chatbot
        self.tools = tools

        thread_id = uuid4()
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
        print(len(messages))
        return {"messages": [*messages, response]}

    def __route_model_output(self, state: State) -> Literal["__end__", "tools"]:
        last_message = state["messages"][-1]
        if not isinstance(last_message, AIMessage):
            raise ValueError(f"Expected AIMessage in output edges, but got {type(last_message).__name__}")

        if not last_message.tool_calls:
            return "__end__"
        return "tools"

    def run(self, message: str) -> dict[str, Any] | Any:
        msg = HumanMessage(content=message)
        return self.app.invoke({"messages": [msg]}, config=self.config)
