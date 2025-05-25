from flask import Flask, request, send_file, render_template
import os
import yt_dlp as youtube_dl
import time
import uuid

app = Flask(__name__)

def search_youtube(query):
    ydl_opts = {
        'quiet': True,
        'skip_download': True,
        'default_search': 'ytsearch1',
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(query, download=False)
        if 'entries' in info and len(info['entries']) > 0:
            video = info['entries'][0]
            return {
                "title": video.get('title'),
                "url": video.get('webpage_url')
            }
        else:
            return None

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        query = request.form["query"]
        media_type = request.form["media_type"]  # "audio" or "video"
        result = search_youtube(query)
        if not result:
            return "No results found."
        
        url = result["url"]
        filename = f"{uuid.uuid4().hex}"

        if media_type == "audio":
            filename += ".m4a"
            ydl_opts = {
                "format": "bestaudio[ext=m4a]",
                "outtmpl": filename,
                "quiet": True,
            }
        else:  # video
            filename += ".mp4"
            ydl_opts = {
                "format": "best[ext=mp4]/best",
                "outtmpl": filename,
                "quiet": True,
            }

        try:
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            return send_file(filename, as_attachment=True)
        except Exception as e:
            return f"Error: {str(e)}"
        finally:
            time.sleep(1)
            if os.path.exists(filename):
                os.remove(filename)
    return render_template("index.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
