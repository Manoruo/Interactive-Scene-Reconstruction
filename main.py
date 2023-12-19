from math import pi, sin, cos

from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from direct.actor.Actor import Actor
from direct.interval.IntervalGlobal import Sequence
from panda3d.core import Point3
from utils.pandas3d_utils import getModelFile 
from utils.asset_downloader import find_and_download_asset
import os
import random
from utils.CVmodels import ObjectDetector



AMOUNT_2_QUERY = 50 
WORLD_CENTER = -8, 42, 0
IMG_TO_ANALYZE = "test_images/plant_left.jpg"

def has_Asset(item_name, folder_path="3DAssets"):
    # Combine the folder path and item name to get the full path
    full_path = os.path.join(folder_path, item_name)

    # Check if the full path (file or folder) exists
    return os.path.exists(full_path)

class MyApp(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        # Disable the camera trackball controls.
        #self.disableMouse()

        # Load the environment model.
        self.scene = self.loader.loadModel("models/environment")
        # Reparent the model to render.
        self.scene.reparentTo(self.render)
        # Apply scale and position transforms on the model.
        self.scene.setScale(5, 5, 5)
        self.scene.setPos(WORLD_CENTER)

        # Add the spinCameraTask procedure to the task manager.
        #self.taskMgr.add(self.spinCameraTask, "SpinCameraTask")
        
        self.start()

    def start(self, img_to_analyze=IMG_TO_ANALYZE):
        
        #image_path = input("Enter the path to an image: ").strip()
        image_path = img_to_analyze
        
        
        OD = ObjectDetector()
        
        objects = OD.getObjects(image_path, confidence_threshold=.5)
        
        for object in objects:
            
            label = object['label']
            position = object['position']
            size = object['size']
            
            self.add_to_scene(label, position)
    
    def add_panda(self):
        # Load and transform the panda actor.
        self.pandaActor = Actor("models/panda-model",
                                {"walk": "models/panda-walk4"})
        self.pandaActor.setScale(0.005, 0.005, 0.005)
        self.pandaActor.reparentTo(self.render)
        # Loop its animation.
        self.pandaActor.loop("walk")

        # Create the four lerp intervals needed for the panda to
        # walk back and forth.
        posInterval1 = self.pandaActor.posInterval(13,
                                                   Point3(0, -10, 0),
                                                   startPos=Point3(0, 10, 0))
        posInterval2 = self.pandaActor.posInterval(13,
                                                   Point3(0, 10, 0),
                                                   startPos=Point3(0, -10, 0))
        hprInterval1 = self.pandaActor.hprInterval(3,
                                                   Point3(180, 0, 0),
                                                   startHpr=Point3(0, 0, 0))
        hprInterval2 = self.pandaActor.hprInterval(3,
                                                   Point3(0, 0, 0),
                                                   startHpr=Point3(180, 0, 0))

        # Create and play the sequence that coordinates the intervals.
        self.pandaPace = Sequence(posInterval1, hprInterval1,
                                  posInterval2, hprInterval2,
                                  name="pandaPace")
        self.pandaPace.loop()

    def add_to_scene(self, item_name, position):
        item_name = item_name.lower()
        if not has_Asset(item_name):
            # download an asset 
            added = find_and_download_asset(item_name, amount=AMOUNT_2_QUERY)
            if not added:
                print("Could not find a model for object {}".format(item_name))
                return
            
        item_file_path = "{}//scene.gltf".format(item_name)
        try:
            
            model = self.loader.load_model(getModelFile(item_file_path))
            model.reparent_to(self.render)
            model.setHpr(0, 90, 0)
            
            model.setPos(position[0], position[1], position[2])
            
            print("Added {} to the scene".format(item_name))
        except:
            print("Could not add {} to the scene. Try again".format(item_name))    
        
    # Define a procedure to move the camera.
    def spinCameraTask(self, task):
        angleDegrees = task.time * 6.0
        angleRadians = angleDegrees * (pi / 180.0)
        self.camera.setPos(22 * sin(angleRadians), -22 * cos(angleRadians), 8)
        self.camera.setHpr(angleDegrees, -10, 0)
        return Task.cont


if __name__ == "__main__":
    
    app = MyApp()
    app.run()