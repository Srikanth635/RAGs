from flask import Flask, request, jsonify
import OntoManager_LGraph
from OntoManager_LGraph import stream_graph_updates, graph_invoke
app = Flask(__name__)

# --- Routes ---

@app.route('/', methods=['GET'])
def home():
    """
    Home route. Returns a welcome message.
    """
    return "<h1>Welcome to the Sample Flask Server!</h1>"


@app.route('/stream', methods=['GET', 'POST'])
def stream():
    """
    Home route. Returns a welcome message.
    """
    if request.method == 'POST':
        data = request.get_json(silent=True)
        if data and 'instruction' in data:
            input_instruction = data['instruction']
        else:
            return jsonify({"error": "Missing 'instruction' in request body"}), 400
    else:  # GET method
        input_instruction = request.args.get('instruction')
        if not input_instruction:
            return jsonify({"error": "Missing 'instruction' parameter"}), 400

    output = stream_graph_updates(input_instruction)


    return str(output)

@app.route('/invoke', methods=['GET', 'POST'])
def invoke():
    """
    Home route. Returns a welcome message.
    """
    if request.method == 'POST':
        data = request.get_json(silent=True)
        if data and 'instruction' in data:
            input_instruction = data['instruction']
        else:
            return jsonify({"error": "Missing 'instruction' in request body"}), 400
    else:  # GET method
        input_instruction = request.args.get('instruction')
        if not input_instruction:
            return jsonify({"error": "Missing 'instruction' parameter"}), 400

    return str(graph_invoke(input_instruction))

# --- Run the app ---

if __name__ == '__main__':
    app.run(debug=True)