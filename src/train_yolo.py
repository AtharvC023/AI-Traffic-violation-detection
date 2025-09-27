from ultralytics import YOLO

model = YOLO('yolov8n.pt')
results = model.train(data='path/to/dataset.yaml', epochs=100)