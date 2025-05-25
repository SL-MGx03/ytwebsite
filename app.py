from flask import Flask, request, send_file, render_template
import os
import yt_dlp
from youtube_search import YoutubeSearch
import uuid
import time

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
        query = request.form.get("query")
        media_type = request.form.get("media_type")
        
        if not query or not media_type:
            return "Missing query or media type", 400
        
        result = search_youtube(query)
        if not result:
            return "No results found."
        
        url = result["url"]
        filename = f"{uuid.uuid4().hex}"

        if media_type == "audio":
            filename += ".m4a"
            ydl_opts = {
                "format": "bestaudio[ext=m4a]/bestaudio",
                "outtmpl": filename,
                "quiet": True,
                "noplaylist": True,
            }
        else:
            filename += ".mp4"
            ydl_opts = {
                "format": "best[ext=mp4]/best",
                "outtmpl": filename,
                "quiet": True,
                "noplaylist": True,
            }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
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
