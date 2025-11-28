from measurementTableDetection import YOLODetector    
detector = YOLODetector()

# Run detection
image_path = "c:\\Users\\Welcome\\Documents\\dicom2pngImages\\494.png"

# Method 1: Get detections as list
detections = detector.detect(image_path)
print(f"Found {len(detections)} detections")

# Method 2: Get detections with formatted output
# detections = detector.detect_and_print(image_path)

# Access individual detections
for det in detections:
    print(f"ROI: {det['bbox']}, Confidence: {det['confidence']:.3f}")