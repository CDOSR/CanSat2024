"""
This module processes data from the CanSat log and saves it in validated 
JSON file
"""
import json
import configparser
import os

def read_configuration(file_path: str = 'config.ini') -> dict:
    """
    Reads configuration from a configuration file.
    
    Parameters:
        file_path (str): The path to the configuration file. Defaults to 'config.ini'.
        
    Returns:
        dict: Configuration parameters.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"{file_path} not found.")

    config = configparser.ConfigParser()
    with open(file_path, 'r', encoding='utf-8') as config_file:
        config.read_file(config_file)

    try:
        return {
            "input_file": config.get('FILE', 'InputFile'),
            "output_file": config.get('FILE', 'OutputFile')
        }

    except configparser.NoOptionError as noe:
        raise ValueError(f"Configuration reading error: {str(noe)}")

def convert_to_json(input_file, output_file):
    """
    Converts a text file with line-separated values to a JSON file.
    
    Parameters:
        input_file (str): The path to the input text file.
        output_file (str): The path to the output JSON file.
    """
    with open(input_file, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    # Clean and convert each line from the input file
    data_list = []
    for line in lines:
        line = line.strip()
        if line:
            try:
                # Convert string representation of dict to actual dict
                data = eval(line.replace("null", "None").replace("true", "True").replace("false", "False"))
                data_list.append(data)
            except Exception as e:
                print(f"Skipping invalid line: {line}. Error {e}")

    # Convert list of dicts to JSON and save to output file
    with open(output_file, 'w', encoding='utf-8') as json_file:
        json.dump(data_list, json_file, indent=4)

# Convert the input file to JSON
# convert_to_json("rcrc24log_770148653.json", "output_data.json")

if __name__ == "__main__":
    config = read_configuration('config.ini')
    input_file = config["input_file"]
    output_file = config["output_file"]
    
    # Convert the input file to JSON
    convert_to_json(input_file, output_file)
