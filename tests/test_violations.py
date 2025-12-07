import unittest
import cv2
import numpy as np
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from local_processor import LocalTrafficProcessor

class TestViolationDetection(unittest.TestCase):
    
    def setUp(self):
        self.processor = LocalTrafficProcessor()
    
    def test_helmet_detection(self):
        """Test helmet violation detection"""
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        motorcycle = {'bbox': [100, 200, 180, 280], 'confidence': 0.8, 'type': 'motorcycle'}
        person = {'bbox': [110, 180, 170, 250], 'confidence': 0.7}
        
        violation = self.processor.check_helmet_violation(frame, motorcycle, [person])
        self.assertIsInstance(violation, bool)
    
    def test_valid_vehicle_detection(self):
        """Test vehicle validation logic"""
        valid = self.processor.is_valid_vehicle_detection([100, 100, 200, 150], 0.8, 2)
        self.assertTrue(valid)
        
        invalid = self.processor.is_valid_vehicle_detection([100, 100, 110, 105], 0.8, 2)
        self.assertFalse(invalid)

if __name__ == '__main__':
    unittest.main()