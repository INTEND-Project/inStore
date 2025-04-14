import getpass
import os

from langchain_core.outputs import GenerationChunk

def _set_env(var: str):
    if not os.environ.get(var):
        os.environ[var] = getpass.getpass(f"{var}: ")

_set_env("NT_BEARER_TOKEN")


####################################

from typing import Annotated

from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

class State(TypedDict):
    messages: Annotated[list, add_messages]

graph_builder = StateGraph(State)

####################################

from typing import Any, Dict, Iterator, List, Mapping, Optional

from langchain_core.callbacks.manager import CallbackManagerForLLMRun
from langchain_core.language_models.llms import LLM
from langchain_core.outputs import GenerationChunk

import requests

class OctoLLM(LLM):

    def _call(
            self,
            prompt: str,                                         
            stop: Optional[List[str]] = None,                     
            run_manager: Optional[CallbackManagerForLLMRun] = None,
            **kwargs: Any) -> str:
        
        url = "http://10.60.26.10/api/chat/completions"
        data = {
            "model": "qwen/qwq-32b",
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            "stream": False,
        }

        headers = {"Authorization": f"Bearer {os.environ.get('NT_BEARER_TOKEN')}"}

        try:
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except requests.exceptions.HTTPError as err:
            print(err)

        if stop is not None:
            raise ValueError("stop kwargs are not permitted")

    def _stream(self, prompt:str, stop: Optional[List[str]]=None, run_manager: Optional[CallbackManagerForLLMRun] = None, **kwargs: Any) -> Iterator[GenerationChunk]:
        for char in prompt[: 10]:
            chunk = GenerationChunk(text=char)
            if run_manager:
                run_manager.on_llm_new_token(chunk.text, chunk=chunk)

            yield chunk

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        return { "model_name": "qwen/qwq-32b" }

    @property
    def _llm_type(self) -> str:
        return "custom"

llm = OctoLLM()
print(llm)


######################
def chatbot(state: State):
    print(state["messages"])
    return { "messages": 
            [
                llm.invoke(state["messages"])
            ]
        }

graph_builder.add_node("chatbot", chatbot)
graph_builder.add_edge(START, "chatbot")

graph_builder.add_edge("chatbot", END)

graph = graph_builder.compile()

###############
def stream_graph_updates(user_input: str):
    for event in graph.stream({"messages": [{"role": "user", "content": user_input}]}):
        for value in event.values():
            print("Assistant:", value["messages"][-1])

while True:
    user_input = input("User: ")
    stream_graph_updates(user_input)

