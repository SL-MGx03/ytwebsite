from flask import Flask, request, send_file, render_template
import os
import youtube_dl
from youtube_search import YoutubeSearch
import time
import uuid

app = Flask(__name__)

def search_youtube(query):
    results = YoutubeSearch(query, max_results=1).to_dict()
    if not results:
        return None
    video = results[0]
    return {
        "title": video["title"],
        "url": f"https://youtube.com{video['url_suffix']}"
    }

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
