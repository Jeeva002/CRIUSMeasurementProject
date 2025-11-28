#!/usr/bin/env python3
"""
YOLOv8 Detector Class
A reusable class for YOLOv8 inference that returns detected ROIs.
"""

from pathlib import Path
from typing import List, Dict, Optional, Tuple
import numpy as np

try:
    from ultralytics import YOLO
except ImportError:
    raise ImportError("Please install ultralytics: pip install ultralytics")


class YOLODetector:
    """
    YOLOv8 Object Detector for measurement table detection.
    
    Attributes:
        model_path (str): Path to the trained YOLO model weights.
        conf_threshold (float): Confidence threshold for detections.
        class_name (str): Name of the class being detected.
    """
    
    def __init__(
        self, 
        model_path: str = "C:\\Users\\Welcome\\Documents\\clarityNLP\\AIFeaturesForGenerativeAIProjectProject\\models\\best.pt",
        conf_threshold: float = 0.5,
        class_name: str = "measurementTable"
    ):
        """
        Initialize the YOLO detector.
        
        Args:
            model_path (str): Path to the trained model weight file.
            conf_threshold (float): Confidence threshold for predictions.
            class_name (str): Name of the detection class.
        """
        self.model_path = model_path
        self.conf_threshold = conf_threshold
        self.class_name = class_name
        self.model = None
        
        self._load_model()
    
    def _load_model(self):
        """Load the YOLO model from the specified path."""
        try:
            self.model = YOLO(self.model_path)
           
        except Exception as e:
            raise RuntimeError(f"Error loading model from {self.model_path}: {e}")
    
    def detect(
        self, 
        image_input,  # Changed from image_path to image_input
    ) -> List[Dict]:
        """
        Run inference on an image and return detected ROIs.
        
        Args:
            image_input: Either a file path (str) or a numpy array/image object
        
        Returns:
            List[Dict]: List of detections, each containing:
                - 'bbox': [x, y, width, height] - Bounding box coordinates
                - 'confidence': float - Detection confidence score
                - 'class_name': str - Class name
                - 'class_id': int - Class ID
                - 'xyxy': [x1, y1, x2, y2] - Corner coordinates
        """
        if self.model is None:
            raise RuntimeError("Model not loaded. Initialize the detector first.")
        
        conf = self.conf_threshold
        
        try:
            # Run inference - YOLO can accept both file paths and numpy arrays
          
            results = self.model(image_input, conf=conf, verbose=False)
        
            
            detections = []
            for r in results:
                if len(r.boxes) > 0:
                    for box in r.boxes:
                        cls_id = int(box.cls[0])
                        confidence = float(box.conf[0])
                        
                        # Get bounding box coordinates
                        xyxy = box.xyxy[0].cpu().numpy().astype(int)
                        x1, y1, x2, y2 = xyxy
                        
                        # Calculate width and height
                        width = x2 - x1
                        height = y2 - y1
                        
                        detection = {
                            'bbox': [int(x1), int(y1), int(width), int(height)],
                            'confidence': confidence,
                            'class_name': self.class_name,
                            'class_id': cls_id,
                            'roi': [int(x1), int(y1), int(x2), int(y2)]
                        }
                        
                        detections.append(detection)
            
            return detections
            
        except Exception as e:
            print(e)
            # raise RuntimeError(f"Inference failed: {e}")
    
    def detect_and_print(self, image_path: str, conf_threshold: Optional[float] = None):
        """
        Run detection and print results in a formatted manner.
        
        Args:
            image_path (str): Path to the input image.
            conf_threshold (float, optional): Override default confidence threshold.
        """
        detections = self.detect(image_path, conf_threshold)
        
        # print(f"\n🔍 Inference on: {Path(image_path).name}")
        # print(f"Confidence threshold: {conf_threshold or self.conf_threshold}")
        # print("=" * 60)
        
        # if detections:
           
         
        #     for i, det in enumerate(detections, 1):
        #         print(f"  {i}. {det['class_name']} (Conf: {det['confidence']:.3f})")
        #         print(f"     Bbox [x, y, w, h]: {det['bbox']}")
        #         print(f"     Corners [x1, y1, x2, y2]: {det['xyxy']}")
        # else:
        #     print("ℹ No detections found above the specified confidence threshold.")
        
        # print("=" * 60)
        
        return detections


