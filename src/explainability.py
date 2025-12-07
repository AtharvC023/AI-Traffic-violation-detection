import cv2
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from ultralytics import YOLO
import torch
import torch.nn.functional as F
from sklearn.metrics import accuracy_score
import os
from datetime import datetime
import json

class ModelExplainer:
    def __init__(self, model_path="yolov8n.pt"):
        self.model = YOLO(model_path)
        
    def generate_grad_cam(self, image, target_class=None):
        """Generate Grad-CAM style heatmap for YOLO detections"""
        # Run inference
        results = self.model(image)
        
        if results[0].boxes is None or len(results[0].boxes) == 0:
            return image, np.zeros((image.shape[0], image.shape[1]))
        
        # Create attention heatmap based on detection boxes
        heatmap = np.zeros((image.shape[0], image.shape[1]))
        
        for box in results[0].boxes:
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
            confidence = float(box.conf[0])
            
            # Create gaussian heatmap around detection
            center_x, center_y = (x1 + x2) // 2, (y1 + y2) // 2
            sigma_x, sigma_y = (x2 - x1) // 4, (y2 - y1) // 4
            
            y_coords, x_coords = np.ogrid[:image.shape[0], :image.shape[1]]
            gaussian = np.exp(-((x_coords - center_x)**2 / (2 * sigma_x**2) + 
                              (y_coords - center_y)**2 / (2 * sigma_y**2)))
            
            heatmap += gaussian * confidence
        
        # Normalize heatmap
        if heatmap.max() > 0:
            heatmap = heatmap / heatmap.max()
        
        return image, heatmap
    
    def create_lime_explanation(self, image, num_samples=100):
        """LIME-style explanation by perturbing image regions"""
        h, w = image.shape[:2]
        segment_size = 32  # Size of segments to perturb
        
        # Get original prediction
        original_results = self.model(image)
        original_detections = len(original_results[0].boxes) if original_results[0].boxes is not None else 0
        
        # Create segments
        segments = []
        importances = []
        
        for y in range(0, h, segment_size):
            for x in range(0, w, segment_size):
                # Create masked image
                masked_image = image.copy()
                y_end = min(y + segment_size, h)
                x_end = min(x + segment_size, w)
                
                # Mask this segment
                masked_image[y:y_end, x:x_end] = 0
                
                # Get prediction on masked image
                masked_results = self.model(masked_image)
                masked_detections = len(masked_results[0].boxes) if masked_results[0].boxes is not None else 0
                
                # Calculate importance (how much detection drops when this region is masked)
                importance = original_detections - masked_detections
                
                segments.append((x, y, x_end, y_end))
                importances.append(importance)
        
        # Normalize importances
        if importances:
            max_importance = max(abs(imp) for imp in importances)
            if max_importance > 0:
                importances = [imp / max_importance for imp in importances]
        
        return segments, importances
    
    def visualize_explanations(self, image_path, save_dir="outputs/explainability"):
        """Generate and save all explanation visualizations"""
        os.makedirs(save_dir, exist_ok=True)
        
        image = cv2.imread(image_path)
        if image is None:
            return None
        
        image_name = os.path.splitext(os.path.basename(image_path))[0]
        
        # 1. Original image with detections
        results = self.model(image)
        annotated_image = results[0].plot()
        
        # 2. Grad-CAM visualization
        _, heatmap = self.generate_grad_cam(image)
        
        # 3. LIME explanation
        segments, importances = self.create_lime_explanation(image)
        
        # Create visualization plots
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle(f'Model Explainability Analysis: {image_name}', fontsize=16)
        
        # Original with detections
        axes[0, 0].imshow(cv2.cvtColor(annotated_image, cv2.COLOR_BGR2RGB))
        axes[0, 0].set_title('Original Detection Results')
        axes[0, 0].axis('off')
        
        # Grad-CAM heatmap
        axes[0, 1].imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        im = axes[0, 1].imshow(heatmap, alpha=0.6, cmap='jet')
        axes[0, 1].set_title('Attention Heatmap (Grad-CAM Style)')
        axes[0, 1].axis('off')
        plt.colorbar(im, ax=axes[0, 1], fraction=0.046, pad=0.04)
        
        # LIME explanation
        lime_viz = image.copy()
        for (x, y, x_end, y_end), importance in zip(segments, importances):
            if importance > 0.1:  # Positive importance (important for detection)
                cv2.rectangle(lime_viz, (x, y), (x_end, y_end), (0, 255, 0), 2)
            elif importance < -0.1:  # Negative importance (hurts detection)
                cv2.rectangle(lime_viz, (x, y), (x_end, y_end), (0, 0, 255), 2)
        
        axes[1, 0].imshow(cv2.cvtColor(lime_viz, cv2.COLOR_BGR2RGB))
        axes[1, 0].set_title('LIME Explanation (Green=Important, Red=Harmful)')
        axes[1, 0].axis('off')
        
        # Feature importance plot
        if importances:
            importance_hist = [imp for imp in importances if abs(imp) > 0.05]
            if importance_hist:
                axes[1, 1].hist(importance_hist, bins=20, alpha=0.7, color='skyblue', edgecolor='black')
                axes[1, 1].set_title('Feature Importance Distribution')
                axes[1, 1].set_xlabel('Importance Score')
                axes[1, 1].set_ylabel('Frequency')
            else:
                axes[1, 1].text(0.5, 0.5, 'No significant features', ha='center', va='center')
                axes[1, 1].set_title('Feature Importance Distribution')
        
        plt.tight_layout()
        
        # Save visualization
        save_path = os.path.join(save_dir, f"{image_name}_explainability.png")
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        # Generate explanation report
        explanation_data = {
            "image": image_name,
            "timestamp": datetime.now().isoformat(),
            "detections_found": len(results[0].boxes) if results[0].boxes is not None else 0,
            "attention_summary": {
                "max_attention": float(heatmap.max()),
                "mean_attention": float(heatmap.mean()),
                "attention_coverage": float((heatmap > 0.1).sum() / heatmap.size)
            },
            "lime_summary": {
                "total_segments": len(segments),
                "important_segments": len([imp for imp in importances if imp > 0.1]),
                "harmful_segments": len([imp for imp in importances if imp < -0.1]),
                "max_importance": max(importances) if importances else 0,
                "min_importance": min(importances) if importances else 0
            }
        }
        
        # Save explanation data
        report_path = os.path.join(save_dir, f"{image_name}_explanation_report.json")
        with open(report_path, 'w') as f:
            json.dump(explanation_data, f, indent=2)
        
        print(f"Explainability analysis saved: {save_path}")
        return explanation_data

def generate_explainability_reports():
    """Generate explainability reports for all sample images"""
    explainer = ModelExplainer()
    sample_dir = "data/samples"
    
    # Process all sample images
    image_files = [f for f in os.listdir(sample_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    
    all_explanations = {}
    for image_file in image_files:
        image_path = os.path.join(sample_dir, image_file)
        explanation = explainer.visualize_explanations(image_path)
        if explanation:
            all_explanations[image_file] = explanation
    
    # Save comprehensive explainability report
    comprehensive_report = {
        "timestamp": datetime.now().isoformat(),
        "total_images_analyzed": len(all_explanations),
        "explanations": all_explanations,
        "summary": {
            "avg_detections": np.mean([exp["detections_found"] for exp in all_explanations.values()]),
            "avg_attention_coverage": np.mean([exp["attention_summary"]["attention_coverage"] for exp in all_explanations.values()]),
            "total_important_segments": sum([exp["lime_summary"]["important_segments"] for exp in all_explanations.values()])
        }
    }
    
    with open("outputs/explainability/comprehensive_explainability_report.json", 'w') as f:
        json.dump(comprehensive_report, f, indent=2)
    
    print("Comprehensive explainability analysis completed!")
    return comprehensive_report

if __name__ == "__main__":
    generate_explainability_reports()