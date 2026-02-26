import os
import re
import json
import subprocess
import tempfile
import threading
from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder='static')
CORS(app)

DOWNLOAD_DIR = tempfile.mkdtemp()

def extract_video_id(url):
    match = re.search(r'(?:v=|youtu\.be/|shorts/)([^&?/\s]{11})', url)
    return match.group(1) if match else None

def is_valid_youtube_url(url):
    return bool(re.search(r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/shorts/)', url))

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

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
        with tempfile.TemporaryDirectory() as tmpdir:
            out_template = os.path.join(tmpdir, '%(title)s.%(ext)s')

            if fmt == 'mp3':
                cmd = [
                    'yt-dlp',
                    '-x', '--audio-format', 'mp3',
                    '--audio-quality', '0',
                    '-o', out_template,
                    '--no-playlist',
                    url
                ]
            else:
                height = quality.replace('p', '')
                cmd = [
                    'yt-dlp',
                    '-f', f'bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]/best[height<={height}][ext=mp4]/best',
                    '--merge-output-format', 'mp4',
                    '-o', out_template,
                    '--no-playlist',
                    url
                ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

            if result.returncode != 0:
                return jsonify({'error': 'Download failed. ' + result.stderr[:200]}), 500

            # Find the downloaded file
            files = os.listdir(tmpdir)
            if not files:
                return jsonify({'error': 'No file was downloaded'}), 500

            filepath = os.path.join(tmpdir, files[0])
            filename = files[0]
            mimetype = 'audio/mpeg' if fmt == 'mp3' else 'video/mp4'

            return send_file(
                filepath,
                as_attachment=True,
                download_name=filename,
                mimetype=mimetype
            )

    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Download timed out (video may be too long)'}), 504
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'service': 'YieldTube API'})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
