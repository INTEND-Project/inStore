import argparse
import json
import re
from typing import Sequence

from dotenv import load_dotenv
from flask import Flask, Response, request
from flask_cors import CORS
from langchain_core.tools import BaseTool
from src.agents import (
    AnalyticsTool,
    Chatbot,
    DataPlacementOptimizerTool,
    SimilarIntentRetriever,
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

    cfg = IntentManagerConfig(cfg=load_config(cfg_path))

    llm = llm_factory(llm_info=cfg.llm_info)

    kg = knowledge_graph_factory(info=cfg.kg_info)
    kg.create_device(
        device_name="EU_DUBLIN_CACHE_1",
        device_type="CACHE",
        max_capacity_gb="256",
        allocated_capacity_gb="121",
        geolocation="dublin",
        backend="minio",
    )

    kg.create_application(application_name="streaming_service")
    kg.create_application(application_name="subscription_service")
    kg.create_application(application_name="account_management_service")

    kg.create_user(user_name="John_Doe")

    tools: Sequence[BaseTool] = [
        DataPlacementOptimizerTool(),
        SimilarIntentRetriever(knowledge_graph=kg),
        TopologyRetriever(knowledge_graph=kg),
        AnalyticsTool(),
    ]

    chatbot = Chatbot(llm=llm, tools=tools)
    w = Workflow(chatbot=chatbot, tools=tools)

    @app.route("/intent", methods=["POST"])
    def add_new_intent():
        j = request.get_json()
        res = w.run(j["intent"])
        for msg in res["messages"]:
            msg.pretty_print()
        return Response(status=200, response=res["messages"])

    app.run(port=5001)


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
