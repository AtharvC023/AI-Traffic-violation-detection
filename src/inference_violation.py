from ultralytics import YOLO
import cv2

model = YOLO('yolov8n.pt')

def detect_violations(video_path):
    cap = cv2.VideoCapture(video_path)
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        results = model(frame)
        # Process violations here
    cap.release()