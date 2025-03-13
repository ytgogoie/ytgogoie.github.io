
import os
import logging
from flask import Flask, render_template, request, jsonify, send_file
from flask_compress import Compress
from utils import get_video_info, download_video

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.secret_key = os.environ.get("SESSION_SECRET", "your-secret-key")
# Add compression
Compress(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/robots.txt')
def robots():
    return send_file('static/robots.txt')

@app.route('/sitemap.xml')
def sitemap():
    return send_file('static/sitemap.xml')

@app.route('/fetch-info', methods=['POST'])
def fetch_info():
    try:
        url = request.form.get('url')
        if not url:
            return jsonify({'error': 'Please provide a valid YouTube URL'}), 400

        video_info = get_video_info(url)
        return jsonify(video_info)
    except Exception as e:
        logger.error(f"Error fetching video info: {str(e)}")
        return jsonify({'error': str(e)}), 400

@app.route('/download', methods=['POST'])
def download():
    try:
        url = request.form.get('url')
        format_id = request.form.get('format')

        if not url or not format_id:
            return jsonify({'error': 'Missing URL or format'}), 400

        # Log the download request
        logger.info(f"Download requested for URL: {url} with format: {format_id}")
        
        download_info = download_video(url, format_id)
        
        # Ensure the download directory exists
        if not os.path.exists(download_info['filepath']):
            logger.error(f"Download failed: File not found at {download_info['filepath']}")
            return jsonify({'error': 'Downloaded file not found'}), 500
            
        logger.info(f"Download successful: {download_info['filename']}")
        
        # Set proper headers to help prevent false antivirus detections
        response = send_file(
            download_info['filepath'],
            as_attachment=True,
            download_name=download_info['filename'],
            mimetype='video/mp4'
        )
        
        # Add security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Content-Security-Policy'] = "default-src 'self'"
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        
        return response
    except Exception as e:
        error_message = str(e)
        logger.error(f"Error downloading video: {error_message}")
        return jsonify({'error': error_message}), 400
