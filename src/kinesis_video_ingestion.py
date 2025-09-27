import boto3
import cv2
from botocore.exceptions import ClientError

class KinesisVideoIngestion:
    def __init__(self, stream_name, region='us-east-1'):
        self.stream_name = stream_name
        self.kvs_client = boto3.client('kinesisvideo', region_name=region)
        
    def ingest_camera_feed(self, camera_url):
        try:
            # Get data endpoint
            response = self.kvs_client.get_data_endpoint(
                StreamName=self.stream_name,
                APIName='PUT_MEDIA'
            )
            endpoint = response['DataEndpoint']
            
            # Create media client
            kvs_media = boto3.client('kinesis-video-media', 
                                   endpoint_url=endpoint)
            
            # Open camera
            cap = cv2.VideoCapture(camera_url)
            
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                    
                # Encode frame
                _, buffer = cv2.imencode('.jpg', frame)
                
                # Send to Kinesis
                kvs_media.put_media(
                    StreamName=self.stream_name,
                    Payload=buffer.tobytes(),
                    ProducerTimestamp=int(time.time() * 1000)
                )
                
        except ClientError as e:
            print(f"Error: {e}")
        finally:
            cap.release()

# Usage
ingestion = KinesisVideoIngestion('traffic-camera-1')
ingestion.ingest_camera_feed('rtsp://camera-ip:554/stream')