import os
import re
import json
from collections import Counter, defaultdict
from flask import Flask, jsonify, send_from_directory, request

# Define the Flask app
app = Flask(__name__)

# Path to the parent folder to monitor
WATCHED_FOLDER = "/Your_RIME_BACKUP_FOLDER"
WATCHED_FILE_NAME = "rime_frost.userdb.txt" # 換成自己使用方案的詞庫檔案名稱

# Global variable to store word frequency for each folder
folder_word_frequencies = defaultdict(Counter)

# List of common words to exclude
# 實驗性功能
EXCLUDE_COMMON_WORDS = {"可以", "這個", "就是", "沒有", "了", "的", "是", "在", "我", "你", "他", "她", "我們", "你們", "他們", "而且", "那個", "啊"}

# Function to parse the Rime dictionary file for a given folder
def parse_rime_file(filepath, folder_name):
    with open(filepath, "r", encoding="utf-8") as file:
        for line in file:
            if not line.startswith("#") and line.strip():
                match = re.match(r"^(.*?)\t(.*?)\tc=(\d+)", line)
                if match:
                    _, word, count = match.groups()
                    if len(word) > 1:  # Exclude single characters
                        folder_word_frequencies[folder_name][word] += int(count)
    print(f"Parsed file: {filepath}")

# Initialize parsing for all existing files
for root, _, files in os.walk(WATCHED_FOLDER):
    if WATCHED_FILE_NAME in files:
        relative_folder = os.path.relpath(root, WATCHED_FOLDER)
        parse_rime_file(os.path.join(root, WATCHED_FILE_NAME), relative_folder)

# Create a 'Total' dataset by merging all folders
total_frequency = Counter()
for freq in folder_word_frequencies.values():
    total_frequency.update(freq)
folder_word_frequencies['Total'] = total_frequency

# Route to serve the main page
@app.route("/")
def index():
    return send_from_directory('.', 'index.html')

# Route to provide data for a specific folder with option to exclude common words
@app.route("/data/<folder>")
def get_folder_data(folder):
    exclude = request.args.get('exclude', 'false').lower() == 'true'
    folder_data = folder_word_frequencies[folder]

    if exclude:
        filtered_data = {word: count for word, count in folder_data.items() if word not in EXCLUDE_COMMON_WORDS}
    else:
        filtered_data = folder_data

    top_words = Counter(filtered_data).most_common(10)
    word_list = [{"word": word, "count": count} for word, count in filtered_data.items()]
    
    return jsonify({
        "words": word_list,
        "top_words": [{"word": word, "count": count} for word, count in top_words]
    })

# Route to get the list of folders
@app.route("/folders")
def get_folders():
    return jsonify({"folders": list(folder_word_frequencies.keys())})

# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True, port=5000)
