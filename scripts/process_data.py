import json
from pathlib import Path

def convert_data_txt_to_full_json():
    txt_path = Path("tests/data.txt")
    json_path = Path("tests/data_full.json")
    
    if not txt_path.exists():
        print("data.txt not found")
        return

    # The file content is already a valid JSON list of points
    with open(txt_path, "r") as f:
        data = json.load(f)
    
    print(f"Total points in data.txt: {len(data)}")
    
    # Let's save it as a clean JSON for easier copy-pasting
    with open(json_path, "w") as fj:
        json.dump(data, fj)
    print(f"Saved to {json_path}")

if __name__ == "__main__":
    convert_data_txt_to_full_json()
