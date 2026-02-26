import os
import re
import json
import subprocess
from flask import Flask, request, jsonify, Response
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

try:
    subprocess.run(['pip', 'install', '--upgrade', 'yt-dlp'], capture_output=True, timeout=60)
except Exception:
    pass

def is_valid_youtube_url(url):
    return bool(re.search(r'(?:youtube\.com/watch|youtu\.be/|youtube\.com/shorts/|youtube\.com/embed/)', url))

@app.route('/')
def index():
    # Try every possible path Render might use
    paths = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'index.html'),
        os.path.join(os.getcwd(), 'static', 'index.html'),
        '/opt/render/project/src/static/index.html',
    ]
    for p in paths:
        if os.path.isfile(p):
            with open(p, 'r') as f:
                return Response(f.read(), mimetype='text/html')
    # Show debug info if file not found
    return jsonify({
        'error': '404 index.html not found',
        'cwd': os.getcwd(),
        'abspath': os.path.dirname(os.path.abspath(__file__)),
        'cwd_files': os.listdir(os.getcwd()),
        'static_exists': os.path.isdir(os.path.join(os.getcwd(), 'static')),
        'static_files': os.listdir(os.path.join(os.getcwd(), 'static')) if os.path.isdir(os.path.join(os.getcwd(), 'static')) else []
    }), 404

@app.route('/api/info', methods=['POST'])
def get_info():
    data = request.get_json()
    url = data.get('url', '').strip()
    if not url or not is_valid_youtube_url(url):
        return jsonify({'error': 'Invalid YouTube URL'}), 400
    try:
        result = subprocess.run(['yt-dlp', '--dump-json', '--no-playlist', url], capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            return jsonify({'error': 'Could not fetch video info. Video may be private or unavailable.'}), 400
        info = json.loads(result.stdout)
        formats = []
        seen_heights = set()
        for f in info.get('formats', []):
            h = f.get('height')
            ext = f.get('ext')
            vcodec = f.get('vcodec', 'none')
            if h and vcodec != 'none' and h not in seen_heights and ext in ('mp4', 'webm'):
                seen_heights.add(h)
                formats.append({'height': h, 'label': f'{h}p'})
        formats = sorted(formats, key=lambda x: x['height'], reverse=True)
        filtered = []
        for s in [2160, 1080, 720, 480]:
            match = next((f for f in formats if f['height'] == s), None)
            if match:
                filtered.append(match)
        duration_sec = info.get('duration', 0)
        duration_str = f"{int(duration_sec // 60)}:{int(duration_sec % 60):02d}" if duration_sec else 'N/A'
        return jsonify({'title': info.get('title', 'Unknown Title'), 'channel': info.get('uploader', 'Unknown Channel'), 'duration': duration_str, 'thumbnail': info.get('thumbnail', ''), 'video_id': info.get('id', ''), 'formats': filtered})
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
        fmt_selector = 'bestaudio[ext=m4a]/bestaudio' if fmt == 'mp3' else f'best[height<={height}][ext=mp4]/best[height<={height}]/best'
        result = subprocess.run(['yt-dlp', '-f', fmt_selector, '--get-url', '--no-playlist', url], capture_output=True, text=True, timeout=25)
        if result.returncode != 0 or not result.stdout.strip():
            result = subprocess.run(['yt-dlp', '-f', 'best', '--get-url', '--no-playlist', url], capture_output=True, text=True, timeout=25)
        if result.returncode != 0 or not result.stdout.strip():
            return jsonify({'error': 'Could not get download URL. Try a different quality.'}), 500
        direct_url = result.stdout.strip().split('\n')[0]
        return jsonify({'download_url': direct_url, 'filename': f'video.{"mp3" if fmt == "mp3" else "mp4"}'})
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Timed out. Try again.'}), 504
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
