from flask import Flask, request, jsonify
from ultralytics import YOLO
import cv2
import numpy as np
import os

app = Flask(__name__)

# Load YOLO model once at startup
model = YOLO("escooter_model.pt")   # your trained model


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

    return escooter_count, bicycle_count


@app.route("/count", methods=["POST"])
def count_endpoint():
    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    img_file = request.files["image"]

    # Save temporarily
    image_path = "uploaded.jpg"
    img_file.save(image_path)

    # Run detection
    escooters, bicycles = count_scooters(image_path)

    return jsonify({
        "electric_scooters": escooters,
        "bicycles": bicycles
    })


@app.route("/", methods=["GET"])
def home():
    return "YOLO Scooter Counter API is running!"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)