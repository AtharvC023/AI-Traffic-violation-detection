"""
Traffic Violation Detection Model
Portable model wrapper for use in any project
"""

import cv2
import numpy as np
from ultralytics import YOLO
from typing import List, Dict, Tuple, Optional
import os


class TrafficViolationModel:
    """
    Wrapper class for YOLOv8n traffic violation detection model
    """
    
    def __init__(self, model_path: str = 'yolov8n.pt', confidence_threshold: float = 0.25):
        """
        Initialize the traffic violation detection model
        
        Args:
            model_path: Path to the YOLOv8n model file
            confidence_threshold: Minimum confidence for detections (0.0-1.0)
        """
        # Get the directory where this file is located
        current_dir = os.path.dirname(os.path.abspath(__file__))
        model_full_path = os.path.join(current_dir, model_path)
        
        # If model doesn't exist in package, try current directory or download
        if not os.path.exists(model_full_path):
            if os.path.exists(model_path):
                model_full_path = model_path
            else:
                # Will download automatically if not found
                model_full_path = model_path
        
        self.model = YOLO(model_full_path)
        self.confidence_threshold = confidence_threshold
        
        # COCO class names (YOLOv8 uses COCO dataset)
        self.class_names = {
            0: 'person', 1: 'bicycle', 2: 'car', 3: 'motorcycle', 4: 'airplane',
            5: 'bus', 6: 'train', 7: 'truck', 8: 'boat', 9: 'traffic light',
            10: 'fire hydrant', 11: 'stop sign', 12: 'parking meter', 13: 'bench'
        }
        
        # Vehicle classes for traffic detection
        self.vehicle_classes = {
            2: 'car',
            3: 'motorcycle',
            5: 'bus',
            7: 'truck',
            1: 'bicycle'
        }
    
    def detect_objects(self, image: np.ndarray, conf: Optional[float] = None) -> List[Dict]:
        """
        Detect objects in an image
        
        Args:
            image: Input image (BGR format from OpenCV)
            conf: Confidence threshold (uses default if None)
            
        Returns:
            List of detected objects with bounding boxes and confidence scores
        """
        if conf is None:
            conf = self.confidence_threshold
        
        results = self.model(image, conf=conf)
        detections = []
        
        for r in results:
            if r.boxes is not None:
                for box in r.boxes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                    confidence = float(box.conf[0])
                    class_id = int(box.cls[0])
                    class_name = self.class_names.get(class_id, f'class_{class_id}')
                    
                    detections.append({
                        'class_id': class_id,
                        'class_name': class_name,
                        'confidence': confidence,
                        'bbox': [int(x1), int(y1), int(x2), int(y2)],
                        'center': [int((x1 + x2) / 2), int((y1 + y2) / 2)]
                    })
        
        return detections
    
    def detect_vehicles(self, image: np.ndarray, conf: Optional[float] = None) -> List[Dict]:
        """
        Detect only vehicles in an image
        
        Args:
            image: Input image (BGR format)
            conf: Confidence threshold
            
        Returns:
            List of detected vehicles
        """
        all_detections = self.detect_objects(image, conf)
        vehicles = []
        
        for det in all_detections:
            if det['class_id'] in self.vehicle_classes:
                det['vehicle_type'] = self.vehicle_classes[det['class_id']]
                vehicles.append(det)
        
        return vehicles
    
    def detect_traffic_lights(self, image: np.ndarray, conf: Optional[float] = None) -> List[Dict]:
        """
        Detect traffic lights in an image
        
        Args:
            image: Input image (BGR format)
            conf: Confidence threshold
            
        Returns:
            List of detected traffic lights
        """
        all_detections = self.detect_objects(image, conf)
        traffic_lights = [det for det in all_detections if det['class_id'] == 9]
        
        # Detect traffic light color (red/yellow/green)
        for light in traffic_lights:
            x1, y1, x2, y2 = light['bbox']
            light_region = image[y1:y2, x1:x2]
            light['color'] = self._detect_light_color(light_region)
        
        return traffic_lights
    
    def _detect_light_color(self, light_region: np.ndarray) -> str:
        """
        Detect traffic light color (red/yellow/green)
        
        Args:
            light_region: Cropped image of traffic light
            
        Returns:
            Color string: 'red', 'yellow', 'green', or 'unknown'
        """
        if light_region.size == 0:
            return 'unknown'
        
        hsv = cv2.cvtColor(light_region, cv2.COLOR_BGR2HSV)
        total_pixels = light_region.shape[0] * light_region.shape[1]
        
        # Red detection
        lower_red1, upper_red1 = (0, 120, 70), (10, 255, 255)
        lower_red2, upper_red2 = (170, 120, 70), (180, 255, 255)
        red_mask = cv2.inRange(hsv, lower_red1, upper_red1) + cv2.inRange(hsv, lower_red2, upper_red2)
        red_pixels = cv2.countNonZero(red_mask)
        
        # Yellow detection
        lower_yellow, upper_yellow = (15, 120, 70), (35, 255, 255)
        yellow_mask = cv2.inRange(hsv, lower_yellow, upper_yellow)
        yellow_pixels = cv2.countNonZero(yellow_mask)
        
        # Green detection
        lower_green, upper_green = (40, 120, 70), (80, 255, 255)
        green_mask = cv2.inRange(hsv, lower_green, upper_green)
        green_pixels = cv2.countNonZero(green_mask)
        
        threshold = total_pixels * 0.08
        
        if red_pixels > threshold and red_pixels > yellow_pixels and red_pixels > green_pixels:
            return 'red'
        elif yellow_pixels > threshold and yellow_pixels > green_pixels:
            return 'yellow'
        elif green_pixels > threshold:
            return 'green'
        
        return 'unknown'
    
    def draw_detections(self, image: np.ndarray, detections: List[Dict], 
                       show_labels: bool = True, show_confidence: bool = True) -> np.ndarray:
        """
        Draw bounding boxes on image
        
        Args:
            image: Input image
            detections: List of detections from detect_objects()
            show_labels: Whether to show class labels
            show_confidence: Whether to show confidence scores
            
        Returns:
            Annotated image
        """
        annotated = image.copy()
        
        # Color map for different classes
        colors = {
            'car': (0, 255, 0),      # Green
            'motorcycle': (255, 0, 255),  # Magenta
            'bus': (0, 255, 255),    # Cyan
            'truck': (255, 255, 0),  # Yellow
            'person': (255, 0, 0),   # Red
            'traffic light': (0, 255, 255),  # Cyan
            'stop sign': (0, 0, 255)  # Red
        }
        
        for det in detections:
            x1, y1, x2, y2 = det['bbox']
            class_name = det['class_name']
            confidence = det['confidence']
            
            # Get color for this class
            color = colors.get(class_name, (128, 128, 128))
            
            # Draw bounding box
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
            
            # Prepare label
            if show_labels or show_confidence:
                label_parts = []
                if show_labels:
                    label_parts.append(class_name)
                if show_confidence:
                    label_parts.append(f'{confidence:.2f}')
                label = ' '.join(label_parts)
                
                # Draw label background
                (text_width, text_height), _ = cv2.getTextSize(
                    label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2
                )
                cv2.rectangle(
                    annotated, 
                    (x1, y1 - text_height - 10), 
                    (x1 + text_width, y1), 
                    color, 
                    -1
                )
                
                # Draw label text
                cv2.putText(
                    annotated, 
                    label, 
                    (x1, y1 - 5), 
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    0.6, 
                    (255, 255, 255), 
                    2
                )
        
        return annotated
    
    def process_video(self, video_path: str, output_path: Optional[str] = None, 
                     frame_skip: int = 1, show_preview: bool = False):
        """
        Process video and detect objects in each frame
        
        Args:
            video_path: Path to input video
            output_path: Path to save annotated video (None = don't save)
            frame_skip: Process every Nth frame (1 = all frames)
            show_preview: Show video preview while processing
        """
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise ValueError(f"Could not open video: {video_path}")
        
        # Get video properties
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Setup video writer if output path provided
        writer = None
        if output_path:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        frame_count = 0
        detections_count = 0
        
        print(f"Processing video: {video_path}")
        print(f"Total frames: {total_frames}, FPS: {fps}, Resolution: {width}x{height}")
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            # Process frame
            if frame_count % frame_skip == 0:
                detections = self.detect_objects(frame)
                detections_count += len(detections)
                
                # Draw detections
                annotated_frame = self.draw_detections(frame, detections)
                
                # Save frame if writer available
                if writer:
                    writer.write(annotated_frame)
                
                # Show preview
                if show_preview:
                    cv2.imshow('Detection Preview', annotated_frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
            
            frame_count += 1
            
            # Progress update
            if frame_count % 30 == 0:
                progress = (frame_count / total_frames) * 100
                print(f"Progress: {progress:.1f}% - Detections: {detections_count}")
        
        cap.release()
        if writer:
            writer.release()
        if show_preview:
            cv2.destroyAllWindows()
        
        print(f"Processing complete! Total detections: {detections_count}")
    
    def get_model_info(self) -> Dict:
        """
        Get information about the model
        
        Returns:
            Dictionary with model information
        """
        return {
            'model_type': 'YOLOv8n',
            'model_size': 'Nano (fastest)',
            'classes': len(self.class_names),
            'vehicle_classes': list(self.vehicle_classes.values()),
            'confidence_threshold': self.confidence_threshold
        }


# Convenience function for quick usage
def load_model(model_path: str = 'yolov8n.pt', confidence: float = 0.25) -> TrafficViolationModel:
    """
    Quick function to load the model
    
    Args:
        model_path: Path to model file
        confidence: Confidence threshold
        
    Returns:
        TrafficViolationModel instance
    """
    return TrafficViolationModel(model_path, confidence)

