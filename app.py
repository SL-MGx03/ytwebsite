import os
import time
import uuid
import asyncio
import traceback
import nest_asyncio

from flask import Flask, request, send_file, render_template
from youtube_search import YoutubeSearch
import yt_dlp
from playwright.async_api import async_playwright

# Apply nest_asyncio to allow asyncio event loop re-entry (fix for Heroku)
nest_asyncio.apply()

app = Flask(__name__)

async def prepare_page(url: str) -> str:
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox"]
        )
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto(url)
        # Wait for video element to load (up to 10 seconds)
        await page.wait_for_selector("video", timeout=10000)
        await browser.close()
        return url

def search_youtube(query: str):
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

        # Search YouTube video
        result = search_youtube(query)
        if not result:
            return "No results found."

        video_url = result["url"]

        # Use Playwright to simulate browser, avoid bot detection
        try:
            loop = asyncio.get_event_loop()
            video_url = loop.run_until_complete(prepare_page(video_url))
        except Exception as e:
            tb = traceback.format_exc()
            print("Playwright error traceback:\n", tb)
            return f"Playwright error: {str(e)}"

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
                ydl.download([video_url])

            return send_file(filename, as_attachment=True)
        except Exception as e:
            tb = traceback.format_exc()
            print("yt-dlp error traceback:\n", tb)
            return f"yt-dlp error: {str(e)}"
        finally:
            time.sleep(1)
            if os.path.exists(filename):
                os.remove(filename)

    return render_template("index.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
