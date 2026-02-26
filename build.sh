#!/usr/bin/env bash
# Install ffmpeg (needed by yt-dlp for merging video+audio)
apt-get update && apt-get install -y ffmpeg
pip install -r requirements.txt
