import cv2
import numpy as np

class SmartOptimizer:
    def __init__(self):
        self.frame_buffer = []
        self.last_detection_results = None
        
    def resize_for_processing(self, frame, target_size=416):
        """Resize frame for faster YOLO processing"""
        h, w = frame.shape[:2]
        if max(h, w) > target_size:
            if w > h:
                new_w, new_h = target_size, int(h * target_size / w)
            else:
                new_w, new_h = int(w * target_size / h), target_size
            return cv2.resize(frame, (new_w, new_h))
        return frame
    
    def should_process_full_detection(self, frame_count):
        """Smart detection scheduling"""
        # Full detection every 2nd frame, tracking on others
        return frame_count % 2 == 0
    
    def preprocess_frame(self, frame):
        """Optimize frame before processing"""
        # Convert to RGB once
        return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)