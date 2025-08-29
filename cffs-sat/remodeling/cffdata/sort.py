import json
import jsbeautifier
import os

def sort_and_update_json_file(filepath, output_filepath=None):
    """
    Reads a JSON file, updates specific fields for each item, sorts the list,
    and writes the updated, sorted data to a new or the original file.

    Args:
        filepath (str): The path to the input JSON file.
        output_filepath (str, optional): The path to the output file.
                                          If None, the original file is overwritten.
                                          Defaults to None.
    """
    # Check if the file exists
    if not os.path.exists(filepath):
        print(f"Error: The file '{filepath}' does not exist.")
        return

    # Read the data from the file
    with open(filepath, 'r') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from '{filepath}': {e}")
            return
            
    # Create a new list to store the updated data
    updated_data = []

    # Loop through each item to update specific keys
    for item in data:
        # Create a new dictionary with the desired keys
        new_item = {
            'k': item.get('k'),
            'd': item.get('d'),
            't': item.get('t'),
            'n': item.get('n'),
            'clauses': item.get('clauses'),
            'time': item.get('time'),
            'solution': item.get('solution'),
        }
        updated_data.append(new_item)

    # Sort the new list of dictionaries
    sorted_data = sorted(updated_data, key=lambda x: (x['k'], x['d'], x['t'], -x['n']))

    # Determine the output file path
    if output_filepath is None:
        output_filepath = filepath

    # Write the sorted data to the output file
    # The `json.dump` function handles the formatting and indentation.
    with open(output_filepath, 'w') as f:
            opts = jsbeautifier.default_options()
            opts.indent_size = 2
            f.write(jsbeautifier.beautify(json.dumps(sorted_data), opts))

    print(f"Successfully sorted and updated data saved to '{output_filepath}'")

sort_and_update_json_file('cffdata2.json', 'cffdata2.json')
