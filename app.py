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
        
        # Ultra-simple configuration that works locally
        ydl_opts = {
            'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
            'format': 'worst[ext=mp4]/worst',  # Use lowest quality to avoid issues
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
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