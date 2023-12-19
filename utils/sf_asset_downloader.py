from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
import subprocess
# old version

ACCESS_TOKEN = "ff794bcac8d249328798f40cd621c5d2" # this is the ID used to interact with SketchFab Library 
HEADERS = {
    'Authorization': f'Bearer {ACCESS_TOKEN}'
}




# Replace 'YOUR_OAUTH_ACCESS_TOKEN' with your Sketchfab OAuth access token
access_token = 'YOUR_OAUTH_ACCESS_TOKEN'


def retrieve_model_from_sf(query_item):
    evaluate_asset(get_asset_uid(query_item))
    

def get_asset_uid(search_query):
    # Set up the Selenium WebDriver (make sure to have the appropriate WebDriver for your browser)
    driver = webdriver.Chrome()  # You can use other browsers like Firefox, Edge, etc.

    try:
        # Open the Sketchfab search page
        driver.get(f'https://sketchfab.com/search?features=downloadable&q={search_query}&type=models')

        # Wait for the search results to load (adjust the locator as needed)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'card-model'))
        )

        # Extract data-uid values
        data_uid_elements = driver.find_elements(By.CSS_SELECTOR, '.card-model[data-uid]')
        data_uid_values = [element.get_attribute('data-uid') for element in data_uid_elements]

        return data_uid_values

    finally:
        # Close the browser window
        driver.quit()

def evaluate_asset(asset_uid_list):
    """
        Picks the best asset to download and downloads it 
    """
    for uid in asset_uid_list:
        #url = f'https://api.sketchfab.com/v3/models/{uid}/download'
        
        #response = requests.get(url, headers=HEADERS)
        curl_command = f"curl 'https://api.sketchfab.com/v3/models/{uid}/download' -H 'authorization: Bearer {ACCESS_TOKEN}'"
        
        
        try:
            result = subprocess.run(curl_command, shell=True, check=True, capture_output=True, text=True)
            response_text = result.stdout
            print(response_text)
        except subprocess.CalledProcessError as e:
            print(f"Error: {e}")
            print(f"Response: {e.output}")
        
        try:
            # Construct the curl command
            
            
            #Check if the request was successful
            if response.status_code == 200:
                # we can download the model
                print("We can download this")
                
                # Parse the JSON response
                download_links = response.json()

                # Extract glTF download link
                gltf_download_url = download_links['gltf']['url']
                print("Download URL for glTF:", gltf_download_url)

                # Download the glTF archive
                gltf_response = requests.get(gltf_download_url)

                # Check if the glTF download was successful
                if gltf_response.status_code == 200:
                    # Save the glTF archive locally (you can change the filename as needed)
                    with open('downloaded_model.gltf', 'wb') as file:
                        file.write(gltf_response.content)
                    print("Download complete!")
                    return
                else:
                    print(f"Error downloading glTF: {gltf_response.status_code}, {gltf_response.text}")
            else:
                print(f"Error: {response.status_code}, {response.text}")
        except:
            continue
        
        
        
        

if __name__ == "__main__":
    # example usuage 
    
    # Replace 'your_item_to_search' with the actual item you want to search for
    item_to_search = 'car'

    # Get data-uid values for the specified search query
    uid_values = retrieve_model_from_sf(item_to_search)

