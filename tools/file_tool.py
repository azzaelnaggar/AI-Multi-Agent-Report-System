# tools/file_tool.py
# Creates an outputs/ folder if it doesn’t exist
# Saves JSON files
# Saves text / Markdown files
# It’s simply a file-saving utility for the whole project.
# tools/file_tool.py
import json
import os
from pathlib import Path

# Ensure outputs directory exists
OUTPUT_DIR = "outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def save_json(data: dict, filename: str):
    """Save dictionary to JSON file"""
    if not filename.endswith('.json'):
        filename += '.json'
    
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f" Saved JSON: {filepath}")
        return filepath
    except Exception as e:
        print(f" Error saving JSON {filepath}: {e}")
        return None

def save_text(text: str, filename: str):
    """Save text to file"""
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f" Saved text: {filepath}")
        return filepath
    except Exception as e:
        print(f" Error saving text {filepath}: {e}")
        return None

def load_json(filename: str):
    """Load JSON file"""
    if not filename.endswith('.json'):
        filename += '.json'
    
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f" Error loading JSON {filepath}: {e}")
        return None

def load_text(filename: str):
    """Load text file"""
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f" Error loading text {filepath}: {e}")
        return None