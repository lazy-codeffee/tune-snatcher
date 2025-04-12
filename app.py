from flask import Flask, request, jsonify, send_file, render_template
import os
import yt_dlp
import datetime

app = Flask(__name__)

# Folder to save audio files and history file
DOWNLOAD_FOLDER = "downloads"
HISTORY_FILE = "download_history.txt"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/download", methods=["POST"])
def download():
    try:
        data = request.get_json()
        video_url = data.get("url")
        quality = data.get("quality", "192")
        file_format = data.get("format", "mp3")

        if not video_url:
            return jsonify({"error": "No URL provided"}), 400

        format_options = {
            "mp3": {"codec": "mp3", "ext": "mp3"},
            "wav": {"codec": "wav", "ext": "wav"},
        }

        if file_format not in format_options:
            return jsonify({"error": "Invalid format"}), 400

        output_format = format_options[file_format]

        # If the user selects "Highest Available" (0), remove preferredquality
        if quality == "0" or file_format == "wav":
            quality_option = {}  # No quality restriction for WAV
        else:
            quality_option = {"preferredquality": quality}  # Set user-selected quality

        # Use yt-dlp to download the best audio format and convert to the selected format
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": f"{DOWNLOAD_FOLDER}/%(title)s.%(ext)s",
            "ffmpeg_location": r"C:\\ffmpeg\\bin",  # Ensure FFmpeg is properly set
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": output_format["codec"],
                **quality_option,  # Apply the quality setting dynamically
            }],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            filename = ydl.prepare_filename(info).replace(
                ".webm", f".{output_format['ext']}").replace(
                    ".m4a", f".{output_format['ext']}").replace(
                        ".mp4", f".{output_format['ext']}")
            
        # Log download history
        with open(HISTORY_FILE, "a", encoding="utf-8") as file:
            file.write(f"{datetime.datetime.now()} - {info['title']} ({video_url}) - {file_format.upper()} {quality}Kbps\n")

        return jsonify({"download_url": f"/download_file?filename={os.path.basename(filename)}"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/download_file")
def download_file():
    filename = request.args.get("filename")
    filepath = os.path.join(DOWNLOAD_FOLDER, filename)

    if not os.path.exists(filepath):
        return jsonify({"error": "File not found"}), 404

    return send_file(filepath, as_attachment=True)

@app.route("/history")
def history():
    if not os.path.exists(HISTORY_FILE):
        return jsonify({"history": []})

    with open(HISTORY_FILE, "r") as file:
        history_data = file.readlines()

    return jsonify({"history": history_data})

if __name__ == "__main__":
    app.run(debug=True)
