from typing import Annotated, Any, TypedDict

from langchain_core.messages import HumanMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from .chatbot import Chatbot
from .tools import DataPlacementOptimizerTool


class State(TypedDict):
    messages: Annotated[list[Any], add_messages]


class Workflow:
    state: State = State()

    def __init__(self, data_placement_tool: DataPlacementOptimizerTool, chatbot: Chatbot):
        self.data_placement_tool = data_placement_tool
        self.chatbot = chatbot

        self.agent_node = "agent"
        self.tool_node = "tools"

        tools = ToolNode([self.data_placement_tool])

        workflow = StateGraph(State)
        workflow.add_node(self.agent_node, self.__call_chatbot)
        workflow.add_node(self.tool_node, tools)
        workflow.add_edge(START, self.agent_node)
        workflow.add_conditional_edges(self.agent_node, self.__route_tools)
        workflow.add_edge(self.tool_node, self.agent_node)
        workflow.add_edge(self.agent_node, END)
        self.app = workflow.compile()

    def __call_chatbot(self, state: State):
        messages = state["messages"]
        response = self.chatbot.invoke(messages)
        return {"messages": [response]}

    def __route_tools(self, state: State) -> str:
        ai_message = state["messages"][-1]
        if len(ai_message.tool_calls) > 0:
            return self.tool_node
        return END

    def run(self, message: str) -> dict[str, Any] | Any:
        msg = HumanMessage(content=message)
        return self.app.invoke({"messages": [msg]})
