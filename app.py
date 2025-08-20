from flask import Flask, request, jsonify, send_file, render_template
import yt_dlp
import os
import tempfile
import uuid
import logging
import sys
from werkzeug.utils import secure_filename

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        
        logger.info(f"Attempting to download: {url}")
        try:
            logger.info(f"yt-dlp version: {yt_dlp.version.__version__}")
        except:
            logger.info("yt-dlp version: unknown")
        
        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        
        # Advanced cookie-free bypass strategies based on yt-dlp wiki
        strategies = [
            # Strategy 1: Skip webpage and configs (visitor data approach)
            {
                'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
                'format': 'worst[ext=mp4]/worst',
                'noplaylist': True,
                'quiet': True,
                'extractor_args': {
                    'youtube': {
                        'player_skip': ['webpage', 'configs'],
                        'player_client': ['android_testsuite'],
                    }
                }
            },
            # Strategy 2: TV client (often bypasses restrictions)
            {
                'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
                'format': 'worst[ext=mp4]/worst',
                'noplaylist': True,
                'quiet': True,
                'extractor_args': {
                    'youtube': {
                        'player_client': ['tv_embedded'],
                        'player_skip': ['webpage'],
                    }
                }
            },
            # Strategy 3: Web embedded client
            {
                'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
                'format': 'worst[ext=mp4]/worst',
                'noplaylist': True,
                'quiet': True,
                'extractor_args': {
                    'youtube': {
                        'player_client': ['web_embedded'],
                        'player_skip': ['webpage'],
                    }
                }
            },
            # Strategy 4: Android creator client
            {
                'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
                'format': 'worst[ext=mp4]/worst',
                'noplaylist': True,
                'quiet': True,
                'user_agent': 'com.google.android.youtube/17.31.35 (Linux; U; Android 11) gzip',
                'extractor_args': {
                    'youtube': {
                        'player_client': ['android_creator'],
                        'player_skip': ['webpage'],
                    }
                }
            }
        ]
        
        video_file = None
        title = 'video'
        
        for i, ydl_opts in enumerate(strategies):
            try:
                logger.info(f"Trying strategy {i+1}/{len(strategies)}")
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    # Get video info first
                    info = ydl.extract_info(url, download=False)
                    title = info.get('title', 'video')
                    
                    # Download the video
                    ydl.download([url])
                    
                    # Find the downloaded file
                    files = os.listdir(temp_dir)
                    if files:
                        video_file = os.path.join(temp_dir, files[0])
                        logger.info(f"Success with strategy {i+1}")
                        break
            except Exception as e:
                logger.error(f"Strategy {i+1} failed: {str(e)}")
                if i == len(strategies) - 1:  # Last strategy
                    raise e
                continue
        
        if not video_file:
            return jsonify({'error': 'No se pudo descargar con ninguna estrategia'}), 500
            
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