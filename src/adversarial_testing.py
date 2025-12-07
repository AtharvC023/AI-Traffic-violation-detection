import cv2
import numpy as np
import torch
from ultralytics import YOLO
import json
from datetime import datetime
import os

class AdversarialTester:
    def __init__(self, model_path="yolov8n.pt"):
        self.model = YOLO(model_path)
        self.results = []
        
    def add_noise(self, image, noise_type="gaussian", intensity=0.1):
        """Add different types of noise to test robustness"""
        if noise_type == "gaussian":
            noise = np.random.normal(0, intensity * 255, image.shape).astype(np.uint8)
            return cv2.add(image, noise)
        elif noise_type == "salt_pepper":
            noisy = image.copy()
            prob = intensity
            random_matrix = np.random.random(image.shape[:2])
            noisy[random_matrix < prob/2] = 0
            noisy[random_matrix > 1-prob/2] = 255
            return noisy
        elif noise_type == "blur":
            kernel_size = int(intensity * 20) + 1
            return cv2.GaussianBlur(image, (kernel_size, kernel_size), 0)
        return image
    
    def brightness_bias(self, image, factor=0.5):
        """Test with different brightness levels"""
        return cv2.convertScaleAbs(image, alpha=factor, beta=0)
    
    def weather_simulation(self, image, weather_type="rain"):
        """Simulate weather conditions"""
        if weather_type == "rain":
            rain_drops = np.random.randint(0, 255, (image.shape[0]//10, image.shape[1]//10))
            rain_drops = cv2.resize(rain_drops, (image.shape[1], image.shape[0]))
            rain_drops = cv2.cvtColor(rain_drops, cv2.COLOR_GRAY2BGR)
            return cv2.addWeighted(image, 0.8, rain_drops, 0.2, 0)
        elif weather_type == "fog":
            fog = np.ones_like(image) * 200
            return cv2.addWeighted(image, 0.7, fog, 0.3, 0)
        return image
    
    def test_adversarial_inputs(self, image_path):
        """Run comprehensive adversarial tests"""
        original_image = cv2.imread(image_path)
        if original_image is None:
            return None
            
        # Original detection
        original_results = self.model(original_image)
        original_detections = len(original_results[0].boxes) if original_results[0].boxes is not None else 0
        
        test_results = {
            "original": {"detections": original_detections, "confidence": self._get_avg_confidence(original_results)},
            "adversarial_tests": {}
        }
        
        # Test different adversarial conditions
        tests = [
            ("gaussian_noise_low", lambda img: self.add_noise(img, "gaussian", 0.05)),
            ("gaussian_noise_high", lambda img: self.add_noise(img, "gaussian", 0.15)),
            ("salt_pepper", lambda img: self.add_noise(img, "salt_pepper", 0.1)),
            ("blur", lambda img: self.add_noise(img, "blur", 0.3)),
            ("dark_bias", lambda img: self.brightness_bias(img, 0.3)),
            ("bright_bias", lambda img: self.brightness_bias(img, 1.5)),
            ("rain_weather", lambda img: self.weather_simulation(img, "rain")),
            ("fog_weather", lambda img: self.weather_simulation(img, "fog"))
        ]
        
        for test_name, transform in tests:
            modified_image = transform(original_image)
            results = self.model(modified_image)
            detections = len(results[0].boxes) if results[0].boxes is not None else 0
            confidence = self._get_avg_confidence(results)
            
            test_results["adversarial_tests"][test_name] = {
                "detections": detections,
                "confidence": confidence,
                "detection_drop": original_detections - detections,
                "confidence_drop": test_results["original"]["confidence"] - confidence
            }
        
        return test_results
    
    def _get_avg_confidence(self, results):
        """Calculate average confidence of detections"""
        if results[0].boxes is None or len(results[0].boxes) == 0:
            return 0.0
        return float(results[0].boxes.conf.mean())
    
    def generate_bias_report(self, test_results):
        """Generate bias and robustness report"""
        if not test_results:
            return None
            
        report = {
            "timestamp": datetime.now().isoformat(),
            "robustness_score": 0,
            "bias_indicators": [],
            "recommendations": []
        }
        
        # Calculate robustness score
        total_tests = len(test_results["adversarial_tests"])
        stable_tests = 0
        
        for test_name, result in test_results["adversarial_tests"].items():
            detection_stability = 1 - abs(result["detection_drop"]) / max(test_results["original"]["detections"], 1)
            confidence_stability = 1 - abs(result["confidence_drop"]) / max(test_results["original"]["confidence"], 0.1)
            
            if detection_stability > 0.7 and confidence_stability > 0.7:
                stable_tests += 1
            
            # Identify bias indicators
            if result["detection_drop"] > 2:
                report["bias_indicators"].append(f"High detection drop in {test_name}")
            if result["confidence_drop"] > 0.3:
                report["bias_indicators"].append(f"High confidence drop in {test_name}")
        
        report["robustness_score"] = stable_tests / total_tests
        
        # Generate recommendations
        if report["robustness_score"] < 0.6:
            report["recommendations"].append("Model needs data augmentation training")
        if any("dark_bias" in indicator for indicator in report["bias_indicators"]):
            report["recommendations"].append("Add low-light training data")
        if any("weather" in indicator for indicator in report["bias_indicators"]):
            report["recommendations"].append("Include weather condition training data")
            
        return report

def run_adversarial_tests():
    """Run adversarial tests on sample images"""
    tester = AdversarialTester()
    sample_dir = "data/samples"
    results_dir = "outputs/adversarial_tests"
    
    os.makedirs(results_dir, exist_ok=True)
    
    # Test on sample images
    image_files = [f for f in os.listdir(sample_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    
    all_results = {}
    for image_file in image_files:
        image_path = os.path.join(sample_dir, image_file)
        test_results = tester.test_adversarial_inputs(image_path)
        if test_results:
            all_results[image_file] = test_results
            
            # Generate individual bias report
            bias_report = tester.generate_bias_report(test_results)
            if bias_report:
                report_path = os.path.join(results_dir, f"{image_file}_bias_report.json")
                with open(report_path, 'w') as f:
                    json.dump(bias_report, f, indent=2)
    
    # Save comprehensive results
    with open(os.path.join(results_dir, "adversarial_test_results.json"), 'w') as f:
        json.dump(all_results, f, indent=2)
    
    print(f"Adversarial testing completed. Results saved in {results_dir}")
    return all_results

if __name__ == "__main__":
    run_adversarial_tests()