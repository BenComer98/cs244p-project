from ultralytics import YOLO
import cv2
import numpy as np
import os

model = YOLO("escooter_model.pt")

def test_model(image_path):
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