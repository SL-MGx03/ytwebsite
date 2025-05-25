from flask import Flask, request, send_file, render_template
import os
import yt_dlp
import time
import uuid

app = Flask(__name__)

def search_youtube(query):
    search_url = f"ytsearch1:{query}"
    ydl_opts = {"quiet": True, "skip_download": True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(search_url, download=False)
        if not info or "entries" not in info or not info["entries"]:
            return None
        video = info["entries"][0]
        return {
            "title": video["title"],
            "url": f"https://youtube.com/watch?v={video['id']}"
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
                "format": "bestaudio[ext=m4a]/bestaudio",
                "outtmpl": filename,
                "quiet": True,
            }
        else:  # video
            filename += ".mp4"
            ydl_opts = {
                "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
                "outtmpl": filename,
                "quiet": True,
                "merge_output_format": "mp4"
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
