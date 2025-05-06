import json

from dotenv import load_dotenv
from flask import Flask, Response, request
from flask_cors import CORS

from pkg.llms import llm_factory

from .agents import Chatbot, DataPlacementOptimizerTool, Workflow
from .config import IntentManagerConfig


def main():
    app = Flask(__name__)
    CORS(app)

    load_dotenv()

    cfg = IntentManagerConfig(cfg=load_config("intents/config.json"))

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
        return Response(status=200, response=res["messages"][-1].content)

    app.run(port=5001)


def load_config(file_path: str):
    with open(file_path, "r") as file:
        data = json.load(file)
        return data


if __name__ == "__main__":
    main()
