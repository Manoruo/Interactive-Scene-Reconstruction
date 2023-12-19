from models import ObjectDetector

# Example usage
if __name__ == "__main__":
    object_detector = ObjectDetector()
    image_path = "C:/Users/Mikea/Computer_Vision_Project/Interactive-Scene-Reconstruction/depth/plant_left.jpg"  # Replace with the path to your image
    detected_objects = object_detector.getObjects(image_path)
    print("Detected Objects:")
    for obj in detected_objects:
        print(obj)
