import pickle
import json
from pathlib import Path

def convert_pkl_to_json():
    pkl_path = Path("tests/peaks.pkl")
    json_path = Path("tests/peaks_example.json")
    
    if not pkl_path.exists():
        print("pkl not found")
        return

    with open(pkl_path, "rb") as f:
        data = pickle.load(f)
    
    # data is likely a list of lists or similar
    # Let's take the first measurement
    if isinstance(data, list) and len(data) > 0:
        first_obs = data[0]
        # Format for HeartScan API: list of {"ax", "ay", "az", "timestamp"}
        # But our pkl might only have peaks. Let's see.
        print(f"Data type: {type(first_obs)}")
        
        # If it's a list of peaks, we need to wrap it.
        # But wait, the user said "az_data_array".
        # Let's just save the raw structure to JSON so I can read it.
        with open(json_path, "w") as fj:
            json.dump(data[:1], fj) # just one for now
        print(f"Saved to {json_path}")

if __name__ == "__main__":
    convert_pkl_to_json()
