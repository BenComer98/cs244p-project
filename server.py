from flask import Flask, request, jsonify
from ultralytics import YOLO
import cv2
import numpy as np
import os
import boto3

app = Flask(__name__)


# model = YOLO("escooter_model.pt")

dynamodb = boto3.resource('dynamodb', region_name='us-west-1')
table = dynamodb.Table('Parking_Count')

def update_dynamodb(location_id, count):
    try:
        response = table.update_item(Key={'location_id': location_id},UpdateExpression='SET #count >
        print(f"Successfully updated DynamoDB: {response}")
        return response
    except Exception as e:
        print(f"Error updating DynamoDB: {str(e)}")
        raise

# def count_scooters(image_path):
#     image = cv2.imread(image_path)
#     results = model(image, conf=0.5, verbose=False)

#     escooter_count = 0
#     bicycle_count = 0

#     for result in results:
#         boxes = result.boxes

#         for box in boxes:
#             class_id = int(box.cls[0])
#             class_name = model.names[class_id]

#             print(class_name)
#             if class_name == 'electric_scooter':
#                 escooter_count += 1
#             elif class_name == 'bicycle':
#                 bicycle_count += 1

#     return escooter_count, bicycle_count

@app.route("/upload", methods=["POST"])
def count_endpoint():
    print(request.data)
    if "location_id" not in request.args:
        print("Location ID not found!")
        return jsonify({"error": "No location_id specified. Add to header."}), 400
    if not request.data:
        print("Image file not found!")
        return jsonify({"error": "No image uploaded"}), 400

    location_id = request.args["location_id"]
    img_bytes = request.data

    print(location_id)

    # Save temporarily
    image_path = f"uploaded_{location_id}.jpg"
    with open(image_path, "wb") as f:
        f.write(img_bytes)

    print(f"Image saved to {image_path}")

    # # Run detection
    # escooters, bicycles = count_scooters(image_path)

    update_dynamodb(location_id, 2)

    return jsonify({
        "message": "Uploaded to DynamoDB!"
    }), 200


@app.route("/", methods=["GET"])
def home():
    return "YOLO Scooter Counter API is running!"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

