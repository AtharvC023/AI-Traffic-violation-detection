# Quick Start Guide

## Installation

1. **Copy the entire `model_package` folder** to your new project directory

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Basic Usage

### Simple Detection

```python
from traffic_model import TrafficViolationModel
import cv2

# Load model
model = TrafficViolationModel()

# Load image
image = cv2.imread('your_image.jpg')

# Detect objects
detections = model.detect_objects(image)

# Print results
for det in detections:
    print(f"{det['class_name']}: {det['confidence']:.2f}")

# Draw and save
annotated = model.draw_detections(image, detections)
cv2.imwrite('output.jpg', annotated)
```

### Vehicle Detection Only

```python
from traffic_model import TrafficViolationModel
import cv2

model = TrafficViolationModel()
image = cv2.imread('traffic_image.jpg')

# Detect only vehicles
vehicles = model.detect_vehicles(image)
print(f"Found {len(vehicles)} vehicles")

for vehicle in vehicles:
    print(f"  - {vehicle['vehicle_type']}: {vehicle['confidence']:.2f}")
```

### Video Processing

```python
from traffic_model import TrafficViolationModel

model = TrafficViolationModel()

# Process video (every 10th frame for speed)
model.process_video(
    'input_video.mp4',
    output_path='output_video.mp4',
    frame_skip=10
)
```

### Real-time Webcam Detection

```python
from traffic_model import TrafficViolationModel
import cv2

model = TrafficViolationModel()
cap = cv2.VideoCapture(0)  # 0 = default camera

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    detections = model.detect_objects(frame)
    annotated = model.draw_detections(frame, detections)
    
    cv2.imshow('Detection', annotated)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
```

## Model Features

- **Object Detection**: Detects 80 COCO classes
- **Vehicle Detection**: Cars, motorcycles, buses, trucks, bicycles
- **Traffic Light Detection**: With color recognition (red/yellow/green)
- **Person Detection**: For helmet violation detection
- **Customizable Confidence**: Adjust detection sensitivity
- **Video Processing**: Process entire videos with frame skipping
- **Real-time**: Works with webcams and video streams

## Integration Examples

### Flask Web App

```python
from flask import Flask, request, jsonify
from traffic_model import TrafficViolationModel
import cv2
import numpy as np

app = Flask(__name__)
model = TrafficViolationModel()

@app.route('/detect', methods=['POST'])
def detect():
    file = request.files['image']
    img = cv2.imdecode(np.frombuffer(file.read(), np.uint8), cv2.IMREAD_COLOR)
    detections = model.detect_objects(img)
    return jsonify(detections)

if __name__ == '__main__':
    app.run()
```

### FastAPI

```python
from fastapi import FastAPI, UploadFile, File
from traffic_model import TrafficViolationModel
import cv2
import numpy as np

app = FastAPI()
model = TrafficViolationModel()

@app.post("/detect")
async def detect_objects(file: UploadFile = File(...)):
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    detections = model.detect_objects(img)
    return {"detections": detections}
```

## Troubleshooting

**Model not found?**
- Make sure `yolov8n.pt` is in the same directory as `traffic_model.py`
- The model will auto-download if not found (requires internet)

**Out of memory?**
- Reduce image/video resolution
- Increase `frame_skip` for video processing
- Use lower confidence threshold to reduce detections

**Slow performance?**
- Use GPU if available (CUDA)
- Process fewer frames (increase `frame_skip`)
- Reduce image resolution before detection

## Next Steps

- See `example_usage.py` for more examples
- Customize detection logic for your use case
- Integrate into your application

