import cv2
import time

class PerformanceOptimizer:
    def __init__(self):
        self.frame_skip = 2  # Process every 2nd frame
        self.last_detection_time = 0
        self.detection_interval = 0.5  # Run detection every 0.5 seconds
        
    def should_process_frame(self, frame_count):
        """Skip frames for better performance"""
        return frame_count % self.frame_skip == 0
    
    def should_run_detection(self):
        """Limit detection frequency"""
        current_time = time.time()
        if current_time - self.last_detection_time >= self.detection_interval:
            self.last_detection_time = current_time
            return True
        return False
    
    def resize_frame(self, frame, max_width=640):
        """Resize frame for faster processing"""
        height, width = frame.shape[:2]
        if width > max_width:
            ratio = max_width / width
            new_height = int(height * ratio)
            frame = cv2.resize(frame, (max_width, new_height))
        return frame