#Version One
from flask import Flask, jsonify, request
import zmq

app = Flask(__name__)

# ZMQ setup
context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect("tcp://localhost:5555")


@app.route('/LoadData', methods=['POST'])
def LoadDataToQueue():
    try:
        # Recieve parameters (These can be adjusted main ones needed are:
        # action: what needs to be done for now its (copy,delete,move,upload)
        # file name/s: that the action needs to be carried out
        #scheduled time: time the action needs to be carried out
        #location where is the file stored

        json_data = request.get_json()
        action = json_data['action']
        file = json_data['file']
        location = json_data['location']
        scheduled_time = json_data['datetime']
    except KeyError as e:
        #error message
        return jsonify({"error": f"Missing required parameter: {e}"}), 400

    # Check if destination is required
    if action in ['move', 'copy']:
        try:
            destination = json_data['destination']
        except KeyError:
            return jsonify({"error": "Destination is required for 'move' and 'copy' actions"}), 400
        if not destination.strip():
            return jsonify({"error": "Destination cannot be an empty string"}), 400

    # Schedule or execute immediately
    if scheduled_time:
        # Placeholder for scheduling logic (implement with RQ/Redis or other scheduling mechanism)
        return jsonify({"message": f"Action '{action}' for file '{file}' scheduled at {scheduled_time}"}), 202
    else:
        # Build message string
        if destination:
            message = f"{action},{file},{location},{destination}"
        else:
            message = f"{action},{file},{location}"

        # Send message via ZMQ (encode to bytes)
        socket.send(message.encode('utf-8'))

        # Receive reply and log
        reply = socket.recv()
        print(
            f"Received reply: {reply.decode('utf-8')} for action '{action}', file '{file}', location '{location}', destination '{destination if destination else 'N/A'}'")

        return jsonify({"reply": reply.decode('utf-8')}), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
