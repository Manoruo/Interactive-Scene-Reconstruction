import requests
import shutil
import os
import requests


import tkinter as tk
from itertools import cycle
from PIL import Image, ImageTk
import requests
from io import BytesIO


API_TOKEN = "ff794bcac8d249328798f40cd621c5d2"
DEFAULT_SAVE_FOLDER = "/3DAssets" # put this in configs
__API_TOKEN = ""
DOWNLOAD_URL = "https://api.sketchfab.com/v3/models/{}/download"
API_SEARCH_URL = "https://api.sketchfab.com/v3/search"





class ImagePreview:
    def __init__(self, list_of_image_urls):
        
        master = tk.Tk()
        master.title("Image Selector")
        
        
        self.master = master
        self.list_of_image_urls = list_of_image_urls
        self.image_cycle = cycle(list_of_image_urls)
        self.selected_image = None
        self.current_index = -1 
        
        
        self.label = tk.Label(master, width=300, height=300)
        self.label.pack()

        self.select_button = tk.Button(master, text="Select", command=self.select_image)
        self.select_button.pack(side=tk.LEFT, padx=10)

        self.continue_button = tk.Button(master, text="Continue", command=self.cycle_image)
        self.continue_button.pack(side=tk.RIGHT, padx=10)

        self.photo_image = None
        self.cycle_image()

    def select_image(self):
        self.selected_image = next(self.image_cycle)
        self.master.destroy()

    def cycle_image(self):
        try:
            self.current_index = (self.current_index + 1) % len(self.list_of_image_urls)
            
            image_url = next(self.image_cycle)
            self.photo_image = self.load_image_from_url(image_url)
            self.label.config(image=self.photo_image, width=700, height=600)
        except StopIteration:
            # Handle the case where all images have been cycled
            self.master.destroy()

    def load_image_from_url(self, url):
        try:
            response = requests.get(url)
            img_data = BytesIO(response.content)
            pil_image = Image.open(img_data)
            tk_image = ImageTk.PhotoImage(pil_image)
            return tk_image
        except Exception as e:
            print(f"Error loading image from URL {url}: {e}")
            return None
    
    
    def get_selection(self):
        self.master.mainloop()
        selected_image = self.selected_image
        
        if selected_image:
            print(f"Selected image URL: {selected_image}")
        else:
            print("No image selected.")

        return selected_image, self.current_index
    

def search_results(params):
    """Search for results.

    Keyword arguments:
    params -- Paremeters to use for search,
        see: https://docs.sketchfab.com/data-api/v3/index.html#/search
    """
    r = requests.get(API_SEARCH_URL, params)
    
    data = None
    try:
        data = r.json()
    except ValueError:
        pass

    assert r.ok, f"Search failed: {r.status_code} - {data}"

    return r.json()["results"]


def _get_download_url(uid):
    """Get download url for a model.

    Keyword arguments:
    uid -- The unique identifier of the model.
    """

    print(f"Getting download url for uid {uid}")
    r = requests.get(
        DOWNLOAD_URL.format(uid),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Token {__API_TOKEN}",
        },
    )

    data = None
    try:
        data = r.json()
    except ValueError:
        pass

    assert r.ok, f"Failed to get download url for model {uid}: {r.status_code} - {data}"

    assert "gltf" in data, f"'gltf' field not found in response: {data}"
    gltf = data.get("gltf")

    assert "url" in gltf, f"'url' field not found in response: {data}"
    url = gltf.get("url")

    assert "size" in gltf, f"'size' field not found in response: {data}"
    size = gltf.get("size")

    return {"url": url, "size": size}


def download_model(model_uid, file_path):
    """Download a model.

    Keyword arguments:
    model_uid -- The unique identifier of the model.
    file_path -- The folder to store the downloaded model to. 
    """

    data = _get_download_url(model_uid)

    # Construct path to same directory as download destination
    file_path.replace("\\", "/")
    parts = file_path.split("/")[:-1]
    if len(parts) == 0:
        parts.append(".")

    directory = ""
    for part in parts:
        directory += part + "/"

    assert os.path.exists(directory), f"Download directory '{directory}'' doesn't exist"

    download_path = f"{directory}{model_uid}.zip"

    print(f"Downloading model, size {(data['size'] / (1024 * 1024)):.1f}MB")
    with requests.get(data["url"], stream=True) as r:
        with open(download_path, "wb") as f:
            shutil.copyfileobj(r.raw, f)

    shutil.unpack_archive(download_path, file_path, "zip")
    os.unlink(download_path)

    print(f"Finished downloading to {file_path}")

    return file_path


def set_api_token(api_token):
    global __API_TOKEN
    __API_TOKEN = api_token
    print("Set API Token")

def find_and_download_asset(query_name, saveLocation=DEFAULT_SAVE_FOLDER, amount=1):
    params = {
		"type": "models",
		"q": query_name, # query  
		"downloadable": True,
		"count": amount # amount of objects to download
    }

    # Get a collection of models from the search API
    models = search_results(params)
    
    
    if (len(models) == 0):
        print("No models found")
        return False
    
    img_list = [x['thumbnails']['images'][0]['url'] for x in models]
    a = ImagePreview(img_list)
    selection, idx = a.get_selection()
    print(idx)
    # Downloading requires authentication
    set_api_token(API_TOKEN)
    # Download a model with UID to a folder
    download_model(models[idx]["uid"],  '.'+ saveLocation + "/" + query_name.lower()) 
    return True

if __name__ == "__main__":
    
    find_and_download_asset("apple", amount=5)
    



