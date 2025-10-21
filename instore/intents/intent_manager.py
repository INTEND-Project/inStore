import argparse
import json
import os
from typing import Any, Sequence

from dotenv import load_dotenv
from flask import Flask, Response, request
from flask_cors import CORS
from langchain_core.messages import AIMessage
from langchain_core.tools import BaseTool
from src.agents import (
    AnalyticsTool,
    Chatbot,
    IntentConflictDetector,
    IntentCreator,
    IntentUpdater,
    RecommendationEngine,
    StorageController,
    TopologyRetriever,
    Workflow,
)
from src.config import IntentManagerConfig

from pkg.db import knowledge_graph_factory
from pkg.llms import llm_factory


def main(cfg_path: str):
    app = Flask(__name__)
    CORS(app)

    load_dotenv()
    # environment = os.environ.get("ANALYTICS_ENV", default="6")
    cfg = IntentManagerConfig(cfg=load_config(cfg_path))

    llm = llm_factory(llm_info=cfg.llm_info)

    kg = knowledge_graph_factory(info=cfg.kg_info)

    intent_conflict_detector = IntentConflictDetector(knowledge_graph=kg)
    # TODO (Ali Amin): Use pre-determined cypher queries for intent creation
    tools: Sequence[BaseTool] = [
        RecommendationEngine(),
        intent_conflict_detector,
        IntentUpdater(knowledge_graph=kg),
        StorageController(),
    ]

    chatbot = Chatbot(llm=llm, tools=tools)
    w = Workflow(chatbot=chatbot, tools=tools)

    @app.route("/intent", methods=["POST"])
    def add_new_intent():
        j = request.get_json()
        res = w.run(j)
        tool_calls = []
        cmds = []
        for msg in res["messages"]:
            if isinstance(msg, AIMessage) and msg.tool_calls is not None and len(msg.tool_calls) > 0:
                for call in msg.tool_calls:
                    tool_calls.append(call["name"])
                    if call["name"] == "StorageController":
                        if "StorageController" in tool_calls:
                            cmds = [call["args"]]
                        else:
                            cmds.append(call["args"])

        response = json.dumps(
            {
                "cmds": cmds,
                "tool_calls": tool_calls,
                "reply": res["messages"][-1].content,
            }
        )

        return Response(status=200, response=response)

    @app.route("/intent", methods=["GET"])
    def get_intents():
        res = kg.get_intents()
        return Response(status=200, response=json.dumps(res))

    @app.route("/intent/<name>", methods=["GET"])
    def get_intent(name: str):
        res = kg.get_intent(name)
        return Response(status=200, response=json.dumps(res))

    @app.route("/device/<name>", methods=["GET"])
    def get_device(name: str):
        res = kg.get_device(name)
        return Response(status=200, response=json.dumps(res))

    app.run(host="0.0.0.0", port=5001)


def load_config(file_path: str):
    with open(file_path, "r") as file:
        data = json.load(file)
        return data


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c",
        "--cfg",
        help="config file path",
        type=str,
        default="intents/config.json",
    )
    args = parser.parse_args()
    main(args.cfg)
