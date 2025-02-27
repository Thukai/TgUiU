import json
import tempfile
import os
import random
import string

def json_to_tmp(json_obj, filename=None):
    """Saves a given JSON object to a file with a random name if no filename is provided."""
    if filename is None:
        # Generate a random filename if not provided
        filename = ''.join(random.choices(string.ascii_letters + string.digits, k=8)) + '.json'
    
    # Create a temporary file with the provided or random filename
    temp_file_path = os.path.join(tempfile.gettempdir(), filename)
    
    # Write the JSON object to the file
    with open(temp_file_path, 'w') as temp_file:
        json.dump(json_obj, temp_file, indent=4)
    
    print(f"JSON data saved to: {temp_file_path}")
    return temp_file_path

def read_json_from_file(filename):
    """Reads a JSON file and returns the parsed JSON object."""
    if not os.path.exists(filename):
        raise FileNotFoundError(f"The file {filename} does not exist.")
    
    # Read the file and parse the JSON content
    with open(filename, 'r') as json_file:
        json_data = json.load(json_file)
    
    return json_data

# Example usage
def get_json:
    json_data = read_json_from_file(json_file_path)  # Use the path returned from save_json_to_tempfile
    print(json_data)
    return json_data
except FileNotFoundError as e:
    print(e)
    return {"error":"Json not found!"}



# Example usage
"""
json_data = {
    "name": "Sana Anzyu",
    "description": "A sample description for the video",
    "duration": "PT00H05M04S",
    "thumbnail": "https://example.com/thumbnail.jpg",
}

# Call the function without providing a filename
json_file_path = save_json_to_tempfile(json_data)
"""


