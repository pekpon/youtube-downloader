from flask import Flask, request, jsonify, send_file, render_template
import yt_dlp
import os
import tempfile
import uuid
from werkzeug.utils import secure_filename

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download_video():
    try:
        data = request.get_json()
        url = data.get('url')
        
        if not url:
            return jsonify({'error': 'URL es requerida'}), 400
        
        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        
        # Configure yt-dlp options with anti-bot measures
        ydl_opts = {
            'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
            'format': 'best[height<=720]/best',  # Download best quality up to 720p
            'noplaylist': True,
            'extractaudio': False,
            'embedsubs': False,
            'writesubtitles': False,
            'writeautomaticsub': False,
            # Anti-bot measures
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'referer': 'https://www.youtube.com/',
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web'],
                    'player_skip': ['webpage'],
                }
            },
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-us,en;q=0.5',
                'Accept-Encoding': 'gzip,deflate',
                'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
                'Connection': 'keep-alive',
                'DNT': '1',
            },
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Get video info first
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'video')
            
            # Download the video
            ydl.download([url])
            
            # Find the downloaded file
            files = os.listdir(temp_dir)
            if not files:
                return jsonify({'error': 'Error al descargar el video'}), 500
            
            video_file = os.path.join(temp_dir, files[0])
            
            # Send file and clean up
            def remove_file(response):
                try:
                    os.remove(video_file)
                    os.rmdir(temp_dir)
                except:
                    pass
                return response
            
            return send_file(
                video_file,
                as_attachment=True,
                download_name=secure_filename(f"{title}.mp4"),
                mimetype='video/mp4'
            )
    
    except yt_dlp.DownloadError as e:
        return jsonify({'error': f'Error de descarga: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': f'Error interno: {str(e)}'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(debug=False, host='0.0.0.0', port=port)