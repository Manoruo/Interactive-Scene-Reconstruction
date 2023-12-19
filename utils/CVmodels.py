import cv2
import torch
import numpy as np
from torchvision import transforms as T
from torchvision.models.detection import fasterrcnn_resnet50_fpn
import matplotlib.pyplot as plt
from scipy.interpolate import RectBivariateSpline


class ObjectDetector:
    """
        Responsible for detecting objects and returning meta data about it to be used later 
    """
    def __init__(self):
        # Load the pre-trained Faster R-CNN model
        self.model = fasterrcnn_resnet50_fpn(pretrained=True)
        self.model.eval()
        self.depthEstimator = DepthEstimator()
        
        # Define class names from COCO dataset
        self.COCO_INSTANCE_CATEGORY_NAMES = [
            '__background__', 'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus',
            'train', 'truck', 'boat', 'traffic light', 'fire hydrant', 'N/A', 'stop sign',
            'parking meter', 'bench', 'bird', 'cat', 'dog', 'horse', 'sheep', 'cow',
            'elephant', 'bear', 'zebra', 'giraffe', 'N/A', 'backpack', 'umbrella', 'N/A', 'N/A',
            'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball',
            'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard', 'tennis racket',
            'bottle', 'N/A', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl',
            'banana', 'apple', 'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza',
            'donut', 'cake', 'chair', 'couch', 'potted plant', 'bed', 'N/A', 'table',
            'N/A', 'N/A', 'toilet', 'N/A', 'tv', 'laptop', 'mouse', 'remote', 'keyboard', 'cell phone',
            'microwave', 'oven', 'toaster', 'sink', 'refrigerator', 'N/A', 'book',
            'clock', 'vase', 'scissors', 'teddy bear', 'hair drier', 'toothbrush', 'plate', 'jar'
        ]

    def getObjects(self, image_path, confidence_threshold=0.7):
        # Load the image
        img = cv2.imread(image_path)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        # Define PyTorch Transform
        transform = T.Compose([T.ToTensor()])

        # Transform the image
        img_tensor = transform(img)
        img_tensor = img_tensor.unsqueeze(0)  # Add batch dimension

        # Inference
        with torch.no_grad():
            prediction = self.model(img_tensor)

        # Extract predictions with confidence scores
        boxes = prediction[0]['boxes'].cpu().numpy()
        labels = prediction[0]['labels'].cpu().numpy()
        scores = prediction[0]['scores'].cpu().numpy()

        # Prepare list of objects with label, 2D position, size, and center point
        objects_list = []
        plt.imshow(img)  # Display the original image

        for box, label, score in zip(boxes, labels, scores):
            if score >= confidence_threshold:
                x_min, y_min, x_max, y_max = box
                x_center, y_center = (x_min + x_max) / 2, (y_min + y_max) / 2
                z_center = self.depthEstimator.estimate_depth_at_position(img, (x_center, y_center))

                # Calculate size based on bounding box dimensions and depth estimate
                width = x_max - x_min
                height = y_max - y_min
                estimated_width = width * z_center
                estimated_height = height * z_center

                object_dict = {
                    'label': self.COCO_INSTANCE_CATEGORY_NAMES[label],
                    'position': {'x': x_center, 'y': y_center, 'z': z_center},
                    'size': {'width': estimated_width, 'height': estimated_height},
                    'confidence': score
                }

                objects_list.append(object_dict)

                # Draw bounding box
                plt.gca().add_patch(plt.Rectangle((x_min, y_min), width, height, fill=False, edgecolor='red', linewidth=2))

                # Draw center point
                plt.scatter(x_center, y_center, c='green', s=50, marker='o')

                # put label above text
                plt.text(x_min, y_min - 5, f"{self.COCO_INSTANCE_CATEGORY_NAMES[label]} ({score:.2f})", color='black',
                         fontsize=10, fontweight='bold')

        plt.show()  # Display the image with bounding boxes and center points

        return objects_list
    
class DepthEstimator:
    """
        Helps us find 3d position of objects
    """
    
    def __init__(self):
        # Download the MiDaS model
        self.midas = torch.hub.load('intel-isl/MiDaS', 'MiDaS_small')
        self.midas.to('cpu')
        self.midas.eval()

        # Process image
        transforms = torch.hub.load('intel-isl/MiDaS', 'transforms')
        self.transform = transforms.small_transform

        self.alpha = 0.2
        self.previous_depth = 0.0
        self.depth_scale = 1.0

    def apply_ema_filter(self, current_depth):
        filtered_depth = self.alpha * current_depth + (1 - self.alpha) * self.previous_depth
        self.previous_depth = filtered_depth  # Update the previous depth value
        return filtered_depth

    def depth_to_distance(self, depth_value):
        return 1.0 / (depth_value * self.depth_scale)

    def estimate_depth_at_position(self, rgb_img, position):
        img = rgb_img
        # Process the image
        img_batch = self.transform(img).to('cpu')

        # Make a prediction
        with torch.no_grad():
            prediction = self.midas(img_batch)
            prediction = torch.nn.functional.interpolate(
                prediction.unsqueeze(1),
                size=img.shape[:2],
                mode='bicubic',
                align_corners=False
            ).squeeze()

        output = prediction.cpu().numpy()
        output_norm = cv2.normalize(output, None, 0, 1, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_32F)

        # Extract position coordinates
        pos_x, pos_y = position

        # Create a spline array of non-integer grid
        h, w = output_norm.shape
        x_grid = np.arange(w)
        y_grid = np.arange(h)

        # Create a spline object using the output_norm array
        spline = RectBivariateSpline(y_grid, x_grid, output_norm)

        # Interpolate depth value at the specified position
        depth_at_position = spline(pos_y, pos_x)
        depth_midas = self.depth_to_distance(depth_at_position)
        depth_at_position = (self.apply_ema_filter(depth_midas) / 10)[0][0]

        return depth_at_position
