
#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install ffmpeg
apt-get update
apt-get install -y ffmpeg
