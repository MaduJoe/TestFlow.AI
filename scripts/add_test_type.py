import os
import json

def add_test_type_to_json_files(root_dir):
    count = 0
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.json'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    try:
                        data = json.load(f)
                    except json.JSONDecodeError:
                        print(f'Error parsing {file_path}')
                        continue
                
                # Add test_type field if not already present
                if 'test_type' not in data:
                    data['test_type'] = 'ai_collection'
                    count += 1
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f'Added test_type field to {count} files')

if __name__ == "__main__":
    add_test_type_to_json_files('cases') 