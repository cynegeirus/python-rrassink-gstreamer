#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RRAS Audio Broadcast API
Version: 1.2
Description:
  REST API for managing GStreamer-based audio broadcast streams.
  Provides endpoints to start, stop, and check the status of active streams.
"""

import subprocess
import logging
import os
import re
from flask import Flask, request, jsonify

# -----------------------------------------------------------------------------
# Flask Configuration
# -----------------------------------------------------------------------------
app = Flask(__name__)

GST_BIN = "/usr/bin/gst-launch-1.0"
LOG_FILE = "/var/log/gstreamer_api.log"
PID_FILE = "/tmp/gstreamer.pid"

# -----------------------------------------------------------------------------
# Logging Setup
# -----------------------------------------------------------------------------
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# Utility Functions
# -----------------------------------------------------------------------------
def is_process_running(pid: int) -> bool:
    """Check if a process with given PID is running."""
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def get_current_stream() -> str | None:
    """Detect if there is an active GStreamer process and extract the stream URL."""
    try:
        result = subprocess.check_output(["ps", "aux"], text=True)
        for line in result.splitlines():
            if GST_BIN in line and "souphttpsrc" in line:
                match = re.search(r'location="?([^"\s]+)"?', line)
                if match:
                    return match.group(1)
        return None
    except Exception as e:
        logger.error(f"Error while checking current stream: {e}")
        return None


def stop_stream() -> bool:
    """Stop any active GStreamer stream using the PID file."""
    if not os.path.exists(PID_FILE):
        logger.info("No active stream to stop.")
        return False

    try:
        with open(PID_FILE, "r") as f:
            pid = int(f.read().strip())

        if is_process_running(pid):
            os.kill(pid, 9)
            logger.info(f"Stopped GStreamer process (PID={pid})")
        else:
            logger.warning("PID file exists, but process not running.")

        os.remove(PID_FILE)
        return True
    except Exception as e:
        logger.error(f"Failed to stop stream: {e}")
        return False


def start_stream_pipeline(source: str, iface: str, host: str, port: int, volume: float):
    """Start a new GStreamer pipeline."""
    pipeline = [
        GST_BIN,
        f'souphttpsrc location="{source}"',
        "! mpegaudioparse ! mpg123audiodec",
        f"! volume volume={volume}",
        "! audioconvert ! audioresample",
        "! audio/x-raw,format=S16LE,channels=1,rate=16000",
        "! rrassink priority-audio=15 destination-audio=4 send-frame=7 sender=1 target=4294967295",
        f"! udpsink port={port} multicast-iface={iface} host={host} bind-port={port}",
    ]

    command = " ".join(pipeline)
    logger.info(f"Starting stream: {command}")

    process = subprocess.Popen(command, shell=True)
    with open(PID_FILE, "w") as f:
        f.write(str(process.pid))

    logger.info(f"GStreamer process started (PID={process.pid})")
    return process


# -----------------------------------------------------------------------------
# Flask Endpoints
# -----------------------------------------------------------------------------
@app.route("/start", methods=["POST"])
def start_stream():
    """Start a new audio stream."""
    data = request.get_json(force=True)

    source = data.get("source")
    iface = data.get("multicast_iface", "eno1")
    host = data.get("multicast_host", "239.193.0.52")
    port = int(data.get("multicast_port", 2100))
    volume = float(data.get("volume", 10.0))

    if not source:
        return jsonify({"error": "Missing 'source' parameter"}), 400

    # Stop any currently running stream
    stop_stream()

    try:
        start_stream_pipeline(source, iface, host, port, volume)
        return jsonify({"status": "started", "urlAddress": source}), 200
    except Exception as e:
        logger.error(f"Failed to start stream: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/stop", methods=["POST"])
def stop():
    """Stop the current stream and return the last URL."""
    url = get_current_stream()
    success = stop_stream()

    return jsonify({
        "status": "stopped" if success else "no-active-stream",
        "urlAddress": url
    }), 200


@app.route("/status", methods=["GET"])
def status():
    """Check whether there is an active stream."""
    url = get_current_stream()
    if url:
        return jsonify({"status": "playing", "urlAddress": url}), 200
    return jsonify({"status": "idle", "urlAddress": None}), 200


@app.route("/", methods=["GET"])
def home():
    """Healthcheck and service info."""
    return jsonify({
        "service": "RRAS Audio Broadcast API",
        "version": "1.2"
    }), 200


# -----------------------------------------------------------------------------
# Main Entry
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8081)
