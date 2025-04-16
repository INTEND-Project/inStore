from flask import Flask, request, Response

from .agents.workflow import Workflow
from .agents.tools import DataPlacementOptimizerTool
from .agents.chatbot import Chatbot

def main():
    app = Flask(__name__)
    
    data_placement: DataPlacementOptimizerTool = DataPlacementOptimizerTool()
    chatbot: Chatbot = Chatbot()
    w = Workflow(data_placement_tool=data_placement, chatbot=chatbot)

    @app.route('/intent', methods=['POST'])
    def add_new_intent():
        json = request.get_json()
        print(w.run(json["intent"]))
        return Response(status=200)
    
    app.run(port=5001)

if __name__ == "__main__":
    main()
