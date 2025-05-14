import argparse
import json
import sys

from dotenv import load_dotenv
from flask import Flask, Response, request
from flask_cors import CORS
from src.agents import Chatbot, DataPlacementOptimizerTool, Workflow
from src.config import IntentManagerConfig

from pkg.llms import llm_factory


def main(cfg_path: str):
    app = Flask(__name__)
    CORS(app)

    load_dotenv()

    cfg = IntentManagerConfig(cfg=load_config(cfg_path))

    llm = llm_factory(llm_info=cfg.llm_info)
    chatbot = Chatbot(llm=llm)
    data_placement = DataPlacementOptimizerTool()

    w = Workflow(data_placement_tool=data_placement, chatbot=chatbot)

    @app.route("/intent", methods=["POST"])
    def add_new_intent():
        json = request.get_json()
        res = w.run(json["intent"])
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
