from flask import Blueprint, request, jsonify

from AzureDIConnection.TestConnection import analyze_receipts

flutter_bp = Blueprint('flutter_bp', __name__)

# flutter app will call this endpoint to send image data
@flutter_bp.route('/process_receipt', methods=['POST'])
def send_data():
    data = request.get_json()
    # Process the received data here

    # byte data will be converted to receipt object 
    receipt = analyze_receipts(data)

    # the idea is that the frontend will get processed receipt data to verify 
    return jsonify({"status": "success", "receipt_data": receipt}), 200

# flutter app will call this endpoint to save receipt to mongo after user verifies data
@flutter_bp.route('/save_receipt', methods=['POST'])
def send_data():
    data = request.get_json()
    # Process the received data here

    # call mongo client and post data to mongo

    return jsonify({"status": "success", "data_received": data}), 200


@flutter_bp.route('/get_data', methods=['GET'])
def receive_data():
    # Prepare the data to be sent to the Flutter app
    data = {"message": "Hello from the server!"}
    return jsonify(data), 200