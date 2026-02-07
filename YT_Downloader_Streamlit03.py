import os
import requests
import streamlit as st
import yt_dlp

# =========================
# Helpers
# =========================

def is_direct_video_link(url):
    return url.lower().endswith((".mp4", ".webm", ".mkv", ".mov", ".avi"))


def get_format_string(quality):
    if quality == "Best (Safe)":
        return "best"
    elif quality == "Best (Max Quality)":
        return "bestvideo+bestaudio/best"
    elif quality == "1080p":
        return "best[height<=1080]/best"
    elif quality == "720p":
        return "best[height<=720]/best"


def download_direct_video(url, output_path, progress_bar, status_text):
    try:
        r = requests.get(url, stream=True)
        r.raise_for_status()

        total = int(r.headers.get("content-length", 0))
        downloaded = 0

        with open(output_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total:
                        progress_bar.progress(min(downloaded / total, 1.0))

        status_text.success("✅ Direct video download complete")

    except Exception as e:
        status_text.error(f"❌ Error: {e}")


def download_with_ytdlp(url, output_dir, quality, progress_bar, status_text):

    def hook(d):
        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            downloaded = d.get("downloaded_bytes", 0)
            if total:
                progress_bar.progress(min(downloaded / total, 1.0))
            status_text.info(f"⬇️ Downloading {d.get('_percent_str', '')}")

        elif d["status"] == "finished":
            progress_bar.progress(1.0)
            status_text.success("✅ Download finished")

    ydl_opts = {
        "outtmpl": os.path.join(output_dir, "%(title)s.%(ext)s"),
        "progress_hooks": [hook],
        "noplaylist": True,
        "quiet": True,
    }

    # ---------- AUDIO ONLY ----------
    if quality == "Audio only":
        ydl_opts.update({
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
        })

    # ---------- VIDEO ----------
    else:
        ydl_opts.update({
            "format": get_format_string(quality),
        })

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        status_text.success("✅ yt‑dlp download complete")

    except Exception as e:
        status_text.error(f"❌ Error: {e}")


# =========================
# Streamlit UI
# =========================

st.set_page_config(page_title="Video Downloader", page_icon="🎬", layout="centered")

st.title("🎬 Video Downloader")
st.caption("YouTube • Live Streams • Direct Links")

url = st.text_input("🔗 Enter video URL")

quality = st.selectbox(
    "🎞 Video Quality",
    [
        "Best (Safe)",
        "Best (Max Quality)",
        "1080p",
        "720p",
        "Audio only"
    ]
)

if quality == "Best (Max Quality)":
    st.warning(
        "⚠️ Max Quality may fail for live streams or some videos. "
        "If it fails, use Best (Safe)."
    )

download_dir = st.text_input(
    "📁 Download folder",
    value=os.path.join(os.getcwd(), "downloads")
)

os.makedirs(download_dir, exist_ok=True)

if st.button("⬇️ Download", disabled=not url):
    progress_bar = st.progress(0.0)
    status_text = st.empty()

    if is_direct_video_link(url):
        output_path = os.path.join(download_dir, "video.mp4")
        download_direct_video(url, output_path, progress_bar, status_text)
    else:
        download_with_ytdlp(
            url,
            download_dir,
            quality,
            progress_bar,
            status_text
        )

st.markdown("---")
st.caption("Developed By Janice Chin")