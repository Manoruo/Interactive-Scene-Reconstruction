from panda3d.core import Filename 

MODELS = "C:\\Users\\Mikea\\Computer_Vision_Project\\Interactive-Scene-Reconstruction\\3DAssets\\" # read this from config file probably 

def getModelFile(model_name: str):
    file_path = MODELS + model_name
    print(file_path)
    return Filename.fromOsSpecific(MODELS + model_name)
