import json
import sys
import os
from collections import defaultdict
import re

def generate_table(input_file, k, d):
    output_file = input_file.replace(".json", ".overleaf")

    # Load JSON
    with open(input_file, "r") as f:
        data = json.load(f)

    # Group by t and take the greatest n with a valid solution
    results = defaultdict(int)
    for entry in data:
        if entry["k"] == k and entry["d"] == d:
            sol = entry["solution"]
            if isinstance(sol, list) and len(sol) > 0:  # valid solution
                t = entry["t"]
                n = entry["n"]
                results[t] = max(results[t], n)

    # Write table
    with open(output_file, "w") as f:
        f.write("\tt   &   n\n")
        for t in sorted(results.keys()):
            f.write(f"\t{t:<4d}&{results[t]:4d}  \\\\\n")

    print(f"Table written to {output_file}")


def run_one(folder_type, k, d):
    folder = f"CreateClauses{folder_type}"
    input_file = os.path.join(folder, f"data_k_{k}_d_{d}.json")
    if not os.path.exists(input_file):
        print(f"Error: {input_file} does not exist")
        return
    generate_table(input_file, k, d)


def run_all(folder_type):
    folder = f"CreateClauses{folder_type}"
    if not os.path.isdir(folder):
        print(f"Error: folder {folder} does not exist")
        return

    # Match files like data_k_3_d_2.json
    pattern = re.compile(r"data_k_(\d+)_d_(\d+)\.json$")
    for fname in os.listdir(folder):
        m = pattern.match(fname)
        if m:
            k = int(m.group(1))
            d = int(m.group(2))
            input_file = os.path.join(folder, fname)
            generate_table(input_file, k, d)


if __name__ == "__main__":
    if len(sys.argv) == 4:
        folder_type = sys.argv[1]
        k = int(sys.argv[2])
        d = int(sys.argv[3])
        run_one(folder_type, k, d)
    elif len(sys.argv) == 2:
        folder_type = sys.argv[1]
        run_all(folder_type)
    else:
        print("Usage:")
        print("  python script.py <Type> <k> <d>   # single file")
        print("  python script.py <Type>           # all k,d in folder")
        sys.exit(1)
