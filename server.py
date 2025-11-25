from flask import Flask, request, jsonify
from ultralytics import YOLO
import cv2
import numpy as np
import os
import boto3
from datetime import datetime

app = Flask(__name__)


model = YOLO("escooter_model.pt")

dynamodb = boto3.resource('dynamodb', region_name='us-west-1')
table = dynamodb.Table('Parking_Count')

s3 = boto3.client('s3')
S3_BUCKET = 'scooter-bucket-iot'

def update_dynamodb(location_id, count):
    try:
        response = table.update_item(Key={'location_id': location_id},UpdateExpression='SET #count = :count', ExpressionAttributeNames={"#count": "count"}, ExpressionAttributeValues={":count": count}, ReturnValues="UPDATED_NEW")
        print(f"Successfully updated DynamoDB: {response}")
        return response
    except Exception as e:
        print(f"Error updating DynamoDB: {str(e)}")
        raise

def count_scooters(image_path):
    image = cv2.imread(image_path)
    results = model(image, conf=0.5, verbose=False)

    escooter_count = 0
    bicycle_count = 0

    for result in results:
        boxes = result.boxes

        for box in boxes:
            class_id = int(box.cls[0])
            class_name = model.names[class_id]

            print(class_name)
            if class_name == 'electric_scooter':
                escooter_count += 1
            elif class_name == 'bicycle':
                bicycle_count += 1

    return [escooter_count, bicycle_count]

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
    upload_to_s3 = "upload_to_s3" in request.args and request.args["upload_to_s3"].lower() == "true"
    img_bytes = request.data

    print(location_id)

    # Save temporarily
    image_path = f"uploaded_{location_id}.jpg"
    with open(image_path, "wb") as f:
        f.write(img_bytes)

    print(f"Image saved to {image_path}")

    if upload_to_s3:
        # Upload to S3
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        s3_key = f"uploads/location_{location_id}/{timestamp}.jpg"

        try:
            s3.put_object(Bucket=S3_BUCKET, Key=s3_key, Body=img_bytes, ContentType="image/jpeg")
            print(f"Uploaded image to S3: {s3_key}")
        except Exception as e:
            print(f"Error uploading to S3: {str(e)}")
            return jsonify({"error": "Failed to upload image to S3"}), 500

    # Run detection
    [escooters, bicycles] = count_scooters(image_path)

    update_dynamodb(location_id, escooters + bicycles)

    return jsonify({
        "message": "Uploaded to DynamoDB!"
    }), 200


@app.route("/", methods=["GET"])
def home():
    return "YOLO Scooter Counter API is running!"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)