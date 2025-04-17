from flask import Flask, Response, request

from pkg.interfaces import LLM
from pkg.llms import llm_factory

from .agents import Chatbot, DataPlacementOptimizerTool, Workflow


def main():
    app = Flask(__name__)

    llm: LLM = llm_factory(model_name="octo")
    chatbot = Chatbot(llm=llm)

    data_placement = DataPlacementOptimizerTool()
    w = Workflow(data_placement_tool=data_placement, chatbot=chatbot)

    @app.route("/intent", methods=["POST"])
    def add_new_intent():
        json = request.get_json()
        res = w.run(json["intent"])
        for msg in res["messages"]:
            msg.pretty_print()
        return Response(status=200)

    app.run(port=5001)


if __name__ == "__main__":
    main()
