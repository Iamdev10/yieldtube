import os
import re
import json
import subprocess
import tempfile
import threading
from flask import Flask, request, jsonify, send_file, send_from_directory, Response
from flask_cors import CORS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, static_folder=os.path.join(BASE_DIR, 'static'), static_url_path='')
CORS(app)

# Auto-update yt-dlp on startup to stay current with YouTube changes
try:
    subprocess.run(['pip', 'install', '--upgrade', 'yt-dlp'], capture_output=True, timeout=60)
except Exception:
    pass

DOWNLOAD_DIR = tempfile.mkdtemp()

def extract_video_id(url):
    match = re.search(r'(?:v=|youtu\.be/|shorts/)([^&?/\s]{11})', url)
    return match.group(1) if match else None

def is_valid_youtube_url(url):
    return bool(re.search(r'(?:youtube\.com\/watch|youtu\.be\/|youtube\.com\/shorts\/|youtube\.com\/embed\/)', url))


@app.route('/')
def index():
    possible_paths = [
        os.path.join(BASE_DIR, 'static'),
        '/opt/render/project/src/static',
        os.path.join(os.getcwd(), 'static'),
    ]
    for path in possible_paths:
        if os.path.exists(os.path.join(path, 'index.html')):
            return send_from_directory(path, 'index.html')
    debug_info = {
        'BASE_DIR': BASE_DIR,
        'cwd': os.getcwd(),
        'base_files': os.listdir(BASE_DIR) if os.path.exists(BASE_DIR) else [],
        'static_exists': os.path.exists(os.path.join(BASE_DIR, 'static')),
        'static_files': os.listdir(os.path.join(BASE_DIR, 'static')) if os.path.exists(os.path.join(BASE_DIR, 'static')) else []
    }
    return __import__('flask').jsonify(debug_info), 404

@app.route('/api/info', methods=['POST'])
def get_info():
    data = request.get_json()
    url = data.get('url', '').strip()

    if not url or not is_valid_youtube_url(url):
        return jsonify({'error': 'Invalid YouTube URL'}), 400

    try:
        result = subprocess.run(
            ['yt-dlp', '--dump-json', '--no-playlist', url],
            capture_output=True, text=True, timeout=30
        )

        if result.returncode != 0:
            return jsonify({'error': 'Could not fetch video info. Video may be private or unavailable.'}), 400

        info = json.loads(result.stdout)

        # Extract available formats
        formats = []
        seen_heights = set()
        for f in info.get('formats', []):
            h = f.get('height')
            ext = f.get('ext')
            vcodec = f.get('vcodec', 'none')
            if h and vcodec != 'none' and h not in seen_heights and ext in ('mp4', 'webm'):
                seen_heights.add(h)
                formats.append({
                    'height': h,
                    'label': f'{h}p',
                    'format_id': f.get('format_id')
                })

        formats = sorted(formats, key=lambda x: x['height'], reverse=True)
        # Only keep up to 4K, 1080, 720, 480
        standard = [2160, 1080, 720, 480]
        filtered = []
        for s in standard:
            match = next((f for f in formats if f['height'] == s), None)
            if match:
                filtered.append(match)

        duration_sec = info.get('duration', 0)
        duration_str = f"{int(duration_sec // 60)}:{int(duration_sec % 60):02d}" if duration_sec else 'N/A'

        return jsonify({
            'title': info.get('title', 'Unknown Title'),
            'channel': info.get('uploader', 'Unknown Channel'),
            'duration': duration_str,
            'thumbnail': info.get('thumbnail', ''),
            'video_id': info.get('id', ''),
            'formats': filtered,
            'view_count': info.get('view_count', 0)
        })

    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Request timed out. Try again.'}), 504
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/download', methods=['POST'])
def download_video():
    data = request.get_json()
    url = data.get('url', '').strip()
    quality = data.get('quality', '1080')
    fmt = data.get('format', 'mp4')

    if not url or not is_valid_youtube_url(url):
        return jsonify({'error': 'Invalid URL'}), 400

    try:
        height = str(quality).replace('p', '')

        if fmt == 'mp3':
            # Get best audio stream URL directly
            fmt_selector = 'bestaudio[ext=m4a]/bestaudio'
        else:
            # Get best video+audio combined stream URL (no merging needed = fast)
            fmt_selector = f'best[height<={height}][ext=mp4]/best[height<={height}]/best'

        result = subprocess.run(
            ['yt-dlp', '-f', fmt_selector, '--get-url', '--no-playlist', url],
            capture_output=True, text=True, timeout=25
        )

        if result.returncode != 0 or not result.stdout.strip():
            # Fallback: try getting any best URL
            result = subprocess.run(
                ['yt-dlp', '-f', 'best', '--get-url', '--no-playlist', url],
                capture_output=True, text=True, timeout=25
            )

        if result.returncode != 0 or not result.stdout.strip():
            return jsonify({'error': 'Could not get download URL. Try a different quality.'}), 500

        direct_url = result.stdout.strip().split('\n')[0]

        # Return the direct URL to the frontend — browser downloads it directly
        # This bypasses Render's 30s timeout completely
        return jsonify({
            'download_url': direct_url,
            'filename': f'video.{"mp3" if fmt == "mp3" else "mp4"}'
        })

    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Timed out getting download URL. Try again.'}), 504
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'service': 'YieldTube API'})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
