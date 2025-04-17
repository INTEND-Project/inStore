from flask import Flask, Response, request

from agents.chatbot import Chatbot
from agents.tools import DataPlacementOptimizerTool
from agents.workflow import Workflow


def main():
    app = Flask(__name__)

    data_placement = DataPlacementOptimizerTool()
    c = Chatbot()
    w = Workflow(data_placement_tool=data_placement, chatbot=c)

    @app.route('/intent', methods=['POST'])
    def add_new_intent():
        json = request.get_json()
        res = w.run(json["intent"])
        for msg in res["messages"]:
            msg.pretty_print()
        return Response(status=200)

    app.run(port=5001)

if __name__ == "__main__":
    main()
