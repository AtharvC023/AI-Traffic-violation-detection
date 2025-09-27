import json
import boto3
from ultralytics import YOLO
import cv2
import numpy as np

def lambda_handler(event, context):
    # Initialize YOLO model
    model = YOLO('/opt/ml/model/yolov8n.pt')
    
    # Get image from S3
    s3 = boto3.client('s3')
    bucket = event['bucket']
    key = event['key']
    
    # Download and process image
    obj = s3.get_object(Bucket=bucket, Key=key)
    img_array = np.frombuffer(obj['Body'].read(), np.uint8)
    frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    
    # Run detection
    results = model(frame)
    
    # Extract detections
    detections = []
    for r in results:
        for box in r.boxes:
            detections.append({
                'class': int(box.cls),
                'confidence': float(box.conf),
                'bbox': box.xyxy.tolist()[0]
            })
    
    return {
        'statusCode': 200,
        'body': json.dumps(detections)
    }