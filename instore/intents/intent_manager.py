import argparse
import json
import queue
import threading
from typing import Sequence

from dotenv import load_dotenv
from flask import Flask, Response, request
from flask_cors import CORS
from langchain_core.messages import AIMessage
from langchain_core.tools import BaseTool
from src.agents import Chatbot, IntentDatabase, RecommendationEngine, VideoMover, Workflow
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

    # TODO (Ali Amin): Use pre-determined cypher queries for intent creation
    tools: Sequence[BaseTool] = [
        IntentDatabase(knowledge_graph=kg),
        RecommendationEngine(),
        VideoMover(),
    ]

    chatbot = Chatbot(llm=llm, tools=tools)

    @app.route("/intent", methods=["POST"])
# {"expression": "Hello world", "id": <uuid>}   
    def add_new_intent():
        notify_queue = queue.Queue()

        request_data = request.get_json()

        def _on_tool_call(tool_message: str):
            notification = {"type": "tool_call", "message": tool_message}
            notify_queue.put(json.dumps(notification))

        def generate():
            workflow_result = {}

            def run_workflow(data):
                try:
                    w = Workflow(chatbot=chatbot, tools=tools, on_tool_callback=_on_tool_call)
                    res = w.run(data)
                    workflow_result["final"] = {"type": "response", "reply": res["messages"][-1].content}
                except Exception as e:
                    workflow_result["final"] = {"type": "error", "message": str(e)}
                finally:
                    notify_queue.put(None)  # Signal completion

            thread = threading.Thread(target=run_workflow, args=(request_data,))
            thread.start()

            while True:
                msg = notify_queue.get()
                if msg is None:
                    if "final" in workflow_result:
                        yield f"data: {json.dumps(workflow_result['final'])}\n\n"
                    break
                yield f"data: {msg}\n\n"

        return Response(generate(), mimetype="text/event-stream")

    @app.route("/intent", methods=["GET"])
    def get_intents():
        res = kg.get_intents()
        return Response(status=200, response=json.dumps(res))

    @app.route("/intent/<name>", methods=["GET"])
    def get_intent(name: str):
        res = kg.get_intent(name)
        return Response(status=200, response=json.dumps(res))

    # Doesn't work properly
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
