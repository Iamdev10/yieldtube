# YieldTube 🎬

A professional YouTube video downloader — elegant frontend + Python/Flask backend powered by yt-dlp.

## 🚀 Deploy Free in 10 Minutes (GitHub + Render)

### Step 1 — Push to GitHub

1. Go to [github.com](https://github.com) → **New Repository**
2. Name it `yieldtube`, set to **Public**, click **Create**
3. Upload all these files:
   - `app.py`
   - `requirements.txt`
   - `build.sh`
   - `render.yaml`
   - `Procfile`
   - `static/index.html`

Or use Git:
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/yieldtube.git
git push -u origin main
```

---

### Step 2 — Deploy on Render (Free)

1. Go to [render.com](https://render.com) → Sign up free
2. Click **New +** → **Web Service**
3. Connect your GitHub account → select `yieldtube` repo
4. Fill in settings:
   - **Name:** yieldtube
   - **Environment:** Python
   - **Build Command:** `bash build.sh`
   - **Start Command:** `gunicorn app:app --workers 2 --timeout 120 --bind 0.0.0.0:$PORT`
5. Click **Create Web Service**
6. Wait ~3 minutes for build to finish
7. Your site will be live at: `https://yieldtube.onrender.com`

> ⚠️ **Free tier note:** Render free services spin down after 15 minutes of inactivity. First request may take ~30 seconds to wake up. Upgrade to paid ($7/mo) for always-on.

---

## 📁 Project Structure

```
yieldtube/
├── app.py              # Flask backend (API routes)
├── requirements.txt    # Python dependencies
├── build.sh            # Render build script (installs ffmpeg)
├── render.yaml         # Render deployment config
├── Procfile            # Process definition
└── static/
    └── index.html      # Frontend (served by Flask)
```

## 🔌 API Endpoints

| Method | Route | Description |
|--------|-------|-------------|
| GET | `/` | Serves the frontend |
| POST | `/api/info` | Fetch video title, thumbnail, formats |
| POST | `/api/download` | Download video/audio file |
| GET | `/api/health` | Health check |

### POST `/api/info`
```json
{ "url": "https://youtube.com/watch?v=..." }
```

### POST `/api/download`
```json
{
  "url": "https://youtube.com/watch?v=...",
  "quality": "1080",
  "format": "mp4"
}
```

## 🛠 Run Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Install ffmpeg (required for merging video+audio)
# Mac:
brew install ffmpeg
# Ubuntu/Debian:
sudo apt install ffmpeg

# Run server
python app.py
```

Open `http://localhost:5000`

## ⚖️ Legal Note

This tool is for **personal use only**. Downloading copyrighted content without permission may violate YouTube's Terms of Service and applicable laws. Use responsibly.
