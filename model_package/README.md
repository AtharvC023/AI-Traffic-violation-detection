# Traffic Violation Detection Model Package

This package contains the YOLOv8n model and code for traffic violation detection that can be used in any project.

## Contents

- `yolov8n.pt` - Pre-trained YOLOv8n model (6.5 MB)
- `traffic_model.py` - Model wrapper class with detection methods
- `example_usage.py` - Simple examples showing how to use the model
- `requirements.txt` - Required Python packages

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Use the model:**
   ```python
   from traffic_model import TrafficViolationModel
   
   # Initialize model
   model = TrafficViolationModel()
   
   # Detect objects in an image
   image = cv2.imread('your_image.jpg')
   results = model.detect_objects(image)
   
   # Process video
   model.process_video('your_video.mp4')
   ```

## Model Details

- **Model Type:** YOLOv8n (nano version - fastest)
- **Size:** ~6.5 MB
- **Classes Detected:** 80 COCO classes including:
  - Vehicles: car, motorcycle, bus, truck, bicycle
  - People: person
  - Traffic signs: traffic light, stop sign
  - And more...

## Usage Examples

See `example_usage.py` for complete examples including:
- Image detection
- Video processing
- Real-time detection
- Custom violation detection

## Integration

This model can be integrated into:
- Web applications (Flask, FastAPI, Streamlit)
- Mobile apps
- Desktop applications
- Cloud services
- Edge devices

