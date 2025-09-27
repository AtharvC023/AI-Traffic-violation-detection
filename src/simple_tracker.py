import cv2

class SimpleTracker:
    def __init__(self):
        self.trackers = {}
        self.next_id = 0
    
    def update(self, detections):
        for detection in detections:
            self.trackers[self.next_id] = detection
            self.next_id += 1
        return self.trackers