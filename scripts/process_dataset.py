import csv
import json
from pathlib import Path

def generate_raw_json_dataset():
    csv_path = Path("tests/data/cardiolog_dataset.csv")
    json_path = Path("nextjs/public/dataset.json")
    
    dataset = []
    with open(csv_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                # az_signal is ALREADY the JSON array of real clinical data
                az_values = json.loads(row['az_signal'])
                
                # We simply map it to the structure required by the API
                # Each point: {"az": float, "timestamp": int} as per your realtime_analysis docs
                # (ax and ay omitted if not in source, or set to 0)
                az_data_array = [
                    {"az": val, "timestamp": i * 10} 
                    for i, val in enumerate(az_values)
                ]
                
                dataset.append({
                    "filename": row['filename'],
                    "az_data_array": az_data_array
                })
            except Exception as e:
                print(f"Error processing row {row.get('filename')}: {e}")

    with open(json_path, 'w', encoding='utf-8') as fj:
        json.dump(dataset, fj)
    print(f"Dataset updated in {json_path}. Total records: {len(dataset)}")

if __name__ == "__main__":
    generate_raw_json_dataset()
