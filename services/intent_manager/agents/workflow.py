from langchain_core.messages import AnyMessage, HumanMessage
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, MessagesState, START, END
from typing import List, Annotated, TypedDict, Any

from langgraph.prebuilt import ToolNode

from tools import DataPlacementOptimizerTool
from chatbot import Chatbot


class State(TypedDict):
    messages: Annotated[list[Any], add_messages]


class Workflow:
    state: State = State()

    def __init__(self, data_placement_tool: DataPlacementOptimizerTool, chatbot: Chatbot):
        self.data_placement_tool = data_placement_tool
        self.chatbot = chatbot

        self.AGENT_NODE = "agent" 
        self.TOOL_NODE = "tools"

        tools = ToolNode([self.data_placement_tool])

        workflow = StateGraph(State)
        workflow.add_node(self.AGENT_NODE, self.__call_chatbot)
        workflow.add_node(self.TOOL_NODE, tools)
        workflow.add_edge(START, self.AGENT_NODE)
        workflow.add_conditional_edges(self.AGENT_NODE, self.__route_tools)
        workflow.add_edge(self.TOOL_NODE, self.AGENT_NODE)
        workflow.add_edge(self.AGENT_NODE, END)
        self.app = workflow.compile()

    def __call_chatbot(self, state: State):
        messages = state["messages"]
        response = self.chatbot.invoke(messages)
        return {"messages": [response]}

    def __route_tools(self, state: State) -> str:
        ai_message = state["messages"][-1]
        if len(ai_message.tool_calls) > 0:
            return self.TOOL_NODE
        return END



    def run(self, message: str) -> dict[str, Any] | Any:
        msg = HumanMessage(content=message)
        print(f"state: {self.state}")
        return self.app.invoke({"messages": [msg]})






