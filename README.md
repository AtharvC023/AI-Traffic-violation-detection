# Traffic Violation Detection System

## Setup
```bash
pip install -r requirements.txt
```

## Usage
1. Place sample video in `data/samples/`
2. Run training: `python src/train_yolo.py`
3. Run inference: `python src/inference_violation.py`

## Structure
- `data/samples/` - Input videos
- `models/` - Trained models
- `outputs/violations/` - Detected violations
- `outputs/explainability/` - Analysis results