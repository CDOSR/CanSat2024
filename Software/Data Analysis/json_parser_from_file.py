import json

def convert_to_json(input_file, output_file):
    with open(input_file, "r") as file:
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
            except:
                print(f"Skipping invalid line: {line}")

    # Convert list of dicts to JSON and save to output file
    with open(output_file, "w") as json_file:
        json.dump(data_list, json_file, indent=4)

# Convert the input file to JSON
convert_to_json("rcrc24log_770148653.json", "output_data.json")
