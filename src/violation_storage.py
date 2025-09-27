import boto3
import json
from datetime import datetime
import cv2

class ViolationStorage:
    def __init__(self):
        self.s3 = boto3.client('s3')
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table('traffic-violations')
        
    def save_violation(self, image, vehicle_id, violation_type, location):
        timestamp = datetime.now().isoformat()
        
        # Save image to S3
        image_key = f"violations/{timestamp}_{vehicle_id}.jpg"
        _, buffer = cv2.imencode('.jpg', image)
        
        self.s3.put_object(
            Bucket='traffic-violations-bucket',
            Key=image_key,
            Body=buffer.tobytes(),
            ContentType='image/jpeg'
        )
        
        # Save metadata to DynamoDB
        self.table.put_item(
            Item={
                'violation_id': f"{timestamp}_{vehicle_id}",
                'vehicle_id': vehicle_id,
                'violation_type': violation_type,
                'timestamp': timestamp,
                'location': location,
                'image_url': f"s3://traffic-violations-bucket/{image_key}",
                'status': 'pending_review'
            }
        )
        
        return f"Violation saved: {image_key}"