# Import necessary libraries for the backend
import os
import time
import json
from flask import Flask, jsonify, render_template
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from collections import Counter
import re

# Define the Flask app
app = Flask(__name__)

# Path to monitor
WATCHED_FOLDER = "/Users/bs10081/Library/CloudStorage/GoogleDrive-i@regchien.info/My Drive/Backup/Rime_Sync/iPhone"
WATCHED_FILE = "rime_frost.userdb.txt"

# Global variable to store word frequency
word_frequency = Counter()

# Function to parse the Rime dictionary file and exclude single characters
def parse_rime_file(filepath):
    global word_frequency
    word_frequency = Counter()  # Reset the counter

    with open(filepath, "r", encoding="utf-8") as file:
        for line in file:
            if not line.startswith("#") and line.strip():
                match = re.match(r"^(.*?)\t(.*?)\tc=(\d+)", line)
                if match:
                    _, word, count = match.groups()
                    if len(word) > 1:  # Exclude single characters
                        word_frequency[word] += int(count)

# Watchdog event handler to monitor file changes
class RimeFileHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith(WATCHED_FILE):
            parse_rime_file(os.path.join(WATCHED_FOLDER, WATCHED_FILE))

# Initialize the watchdog observer
observer = Observer()
event_handler = RimeFileHandler()
observer.schedule(event_handler, WATCHED_FOLDER, recursive=False)
observer.start()

# Route to serve the main page
@app.route("/")
def index():
    return """
    <!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rime Input Method Stats</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.7.0/chart.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/wordcloud2.js/1.0.0/wordcloud2.min.js"></script>
    <style>
        body { font-family: Arial, sans-serif; }
        #wordCloudCanvas { width: 100%; height: 500px; }
        .container { width: 80%; margin: auto; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Rime Input Method Stats</h1>
        <h2>Word Cloud</h2>
        <canvas id="wordCloudCanvas"></canvas>
        <h2>Top 10 Most Used Words</h2>
        <canvas id="barChart" width="400" height="200"></canvas>
    </div>

    <script>
        function resizeCanvas() {
            const canvas = document.getElementById('wordCloudCanvas');
            canvas.width = window.innerWidth * 0.8; // 設置為視窗寬度的 80%
            canvas.height = window.innerHeight * 0.5; // 設置為視窗高度的 50%
        }

        // 生成詞雲的函式
        function generateWordCloud(wordList) {
            const canvas = document.getElementById('wordCloudCanvas');
            WordCloud(canvas, {
                list: wordList,
                gridSize: 5,
                weightFactor: 12,
                color: 'random-dark',
                backgroundColor: '#fff',
                rotateRatio: 0.4,
                minRotation: -Math.PI / 6,
                maxRotation: Math.PI / 6,
                shrinkToFit: true,
                fontFamily: 'Arial, sans-serif',
                drawOutOfBound: false
            });
        }

        // Fetch data from the backend
        fetch('/data')
            .then(response => response.json())
            .then(data => {
                const wordData = data.words;
                const topWords = data.top_words;

                // Resize canvas and generate word cloud
                resizeCanvas();
                generateWordCloud(wordData.map(item => [item.word, item.count]));

                // Bar Chart Generation
                const ctx = document.getElementById('barChart').getContext('2d');
                new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: topWords.map(item => item.word),
                        datasets: [{
                            label: 'Usage Count',
                            data: topWords.map(item => item.count),
                            backgroundColor: 'rgba(54, 162, 235, 0.5)',
                            borderColor: 'rgba(54, 162, 235, 1)',
                            borderWidth: 1
                        }]
                    },
                    options: {
                        responsive: true,
                        scales: {
                            y: { beginAtZero: true }
                        }
                    }
                });
            });

        // Resize the canvas when the window is resized
        window.addEventListener('resize', () => {
            resizeCanvas();
            window.location.reload(); // 重新加載頁面以重新生成詞雲
        });
    </script>
</body>
</html>
    
    """

# Route to provide data for the frontend
@app.route("/data")
def get_data():
    top_words = word_frequency.most_common(10)
    word_list = [{"word": word, "count": count} for word, count in word_frequency.items()]
    return jsonify({
        "words": word_list,
        "top_words": [{"word": word, "count": count} for word, count in top_words]
    })

# Run the Flask app
if __name__ == "__main__":
    try:
        # Initial parsing of the file if it exists
        if os.path.exists(os.path.join(WATCHED_FOLDER, WATCHED_FILE)):
            parse_rime_file(os.path.join(WATCHED_FOLDER, WATCHED_FILE))
        app.run(debug=True, port=5000)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
