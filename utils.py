import os
import logging
import yt_dlp
import time
import functools
from datetime import datetime
from urllib.parse import urlparse

# Simple in-memory cache for video info
VIDEO_INFO_CACHE = {}
CACHE_EXPIRY = 3600  # 1 hour in seconds

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create downloads directory if it doesn't exist
DOWNLOAD_DIR = "downloads"
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

def is_valid_youtube_url(url):
    try:
        parsed = urlparse(url)
        return parsed.netloc in ['www.youtube.com', 'youtube.com', 'youtu.be']
    except:
        return False

def format_file_size(bytes):
    """Format file size from bytes to human-readable format"""
    if bytes is None:
        return 'N/A'

    # Convert bytes to megabytes for easier reading
    size_mb = bytes / (1024 * 1024)

    if size_mb < 1:
        # Show in KB if less than 1 MB
        size_kb = bytes / 1024
        return f"{size_kb:.1f} KB"
    else:
        return f"{size_mb:.1f} MB"

def format_resolution(resolution):
    if not resolution or resolution == 'N/A':
        return 'N/A'
    try:
        if 'x' in resolution:
            height = resolution.split('x')[1]
            return f"{height}p"
        return resolution
    except:
        return resolution

def format_duration(seconds):
    """Format duration from seconds to MM:SS or HH:MM:SS"""
    if not seconds:
        return 'Unknown'

    try:
        seconds = int(float(seconds))
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60

        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes}:{seconds:02d}"
    except:
        return 'Unknown'

def get_video_info(url):
    """Get information about a YouTube video."""
    if not is_valid_youtube_url(url):
        raise ValueError("Not a valid YouTube URL")

    # Check cache first
    current_time = time.time()
    if url in VIDEO_INFO_CACHE:
        cache_time, cache_data = VIDEO_INFO_CACHE[url]
        if current_time - cache_time < CACHE_EXPIRY:
            logger.info(f"Using cached info for video: {url}")
            return cache_data

    try:
        logger.info(f"Fetching info for video: {url}")

        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
            'format': 'bestvideo+bestaudio/best',
            'merge_output_format': 'mp4',
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            # Only select these key resolutions
            priority_heights = [360, 480, 720, 1080]
            priority_formats = {}

            # Organize formats by height
            for f in info.get('formats', []):
                if f.get('vcodec') == 'none':
                    continue
                resolution = f.get('resolution', 'N/A')
                ext = f.get('ext', 'N/A')
                format_id = f.get('format_id', '')
                filesize = f.get('filesize')
                height = f.get('height')
                if height:
                    height = int(height)
                    # Only process if the height is in our priority list
                    if height in priority_heights:
                        quality = f"{format_resolution(resolution)} ({ext})"
                        if height not in priority_formats:
                            priority_formats[height] = []
                        priority_formats[height].append({
                            'format_id': format_id,
                            'quality': quality,
                            'ext': ext,
                            'resolution': resolution,
                            'filesize': format_file_size(filesize) if filesize else 'Unknown MB'
                        })

            # Add only the best format for each resolution
            formats = []
            for height in priority_heights:
                if height in priority_formats:
                    # Prefer MP4 format
                    mp4_formats = [f for f in priority_formats[height] if f['ext'] == 'mp4']
                    if mp4_formats:
                        # Take the best MP4 format (usually with the largest filesize)
                        best_format = sorted(mp4_formats, 
                                           key=lambda x: float(x['filesize'].split()[0]) if 'Unknown' not in x['filesize'] else 0, 
                                           reverse=True)[0]
                        formats.append(best_format)
                    else:
                        # If no MP4, take the best available format
                        formats.append(priority_formats[height][0])

            # Format the data for display
            formatted_formats = []
            for fmt in formats:
                # Extract height only for display (like "360p" instead of full resolution)
                resolution_display = format_resolution(fmt['resolution'])
                
                # Check if format has audio
                has_audio = False
                for f in info.get('formats', []):
                    if f.get('format_id') == fmt['format_id'] and f.get('acodec') != 'none':
                        has_audio = True
                        break
                
                # Check if it's a YouTube Shorts URL
                is_shorts = '/shorts/' in url
                
                formatted_formats.append({
                    'format_id': fmt['format_id'],
                    'quality': f"{resolution_display}" if fmt['ext'] == 'mp4' else f"{resolution_display} ({fmt['ext']})",
                    'extension': fmt['ext'],
                    'filesize': fmt['filesize'] if fmt['filesize'] != 'Unknown MB' else '0 MB',
                    'has_audio': True if is_shorts else has_audio
                })

            result = {
                'title': info.get('title', 'Unknown Title'),
                'thumbnail': info.get('thumbnail', ''),
                'duration': info.get('duration'),
                'uploader': info.get('uploader', 'Unknown Uploader'),
                'formats': formatted_formats
            }
            
            # Cache the result
            VIDEO_INFO_CACHE[url] = (time.time(), result)
            
            return result

    except Exception as e:
        logger.error(f"Error fetching video info: {str(e)}")
        raise Exception(f"Error fetching video info: {str(e)}")

def format_resolution(resolution):
    """Format resolution to a user-friendly string."""
    if not resolution or resolution == 'N/A':
        return 'N/A'
    try:
        if 'x' in resolution:
            height = resolution.split('x')[1]
            return f"{height}p"
        return resolution
    except:
        return resolution

def download_video(url, format_id):
    """Download video with the specified format."""
    try:
        logger.info(f"Downloading video: {url} with format: {format_id}")

        # Create a timestamp for unique filenames
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

        # Configure yt-dlp options with metadata to prevent false positives
        ydl_opts = {
            'format': f"{format_id}+bestaudio[ext=m4a]/best",  # Add best audio to the video format
            'outtmpl': f'{DOWNLOAD_DIR}/%(title)s-{timestamp}.%(ext)s',
            'addmetadata': True,  # Add metadata to file
            'writethumbnail': False,  # Don't write thumbnail
            'quiet': False,  # Show progress
            'no_warnings': False,
            'postprocessors': [{
                'key': 'FFmpegEmbedSubtitle'
            }, {
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4'
            }, {
                'key': 'FFmpegMetadata'
            }],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            downloaded_file = ydl.prepare_filename(info)

        # Get just the filename without the directory
        filename = os.path.basename(downloaded_file)

        return {
            'filepath': downloaded_file,
            'filename': filename
        }

    except Exception as e:
        logger.error(f"Error downloading video: {str(e)}")
        raise Exception(f"Error downloading video: {str(e)}")