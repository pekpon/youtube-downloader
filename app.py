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
        
        # Configure yt-dlp options with multiple bypass strategies
        ydl_opts = {
            'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
            'format': '(best[height<=720]/best[height<=480]/worst)[ext=mp4]/(best[height<=720]/best[height<=480]/worst)',
            'noplaylist': True,
            'extractaudio': False,
            'embedsubs': False,
            'writesubtitles': False,
            'writeautomaticsub': False,
            # Multiple anti-bot strategies
            'user_agent': 'Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36',
            'referer': 'https://m.youtube.com/',
            'age_limit': 99,
            'extractor_args': {
                'youtube': {
                    'player_client': ['android_creator', 'android', 'ios', 'web'],
                    'player_skip': ['webpage', 'configs'],
                    'skip': ['hls', 'dash'],
                }
            },
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36',
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
                'X-YouTube-Client-Name': '2',
                'X-YouTube-Client-Version': '2.20210721.00.00',
            },
            'fragment_retries': 10,
            'retries': 10,
        }
        
        # Simplified single strategy approach for Railway
        strategy_opts = {
            **ydl_opts,
            'user_agent': 'Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36',
            'extractor_args': {
                'youtube': {
                    'player_client': ['android'],
                    'player_skip': ['webpage'],
                }
            }
        }
        
        with yt_dlp.YoutubeDL(strategy_opts) as ydl:
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