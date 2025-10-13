# RRAS Audio Broadcast API

A lightweight REST API for managing **GStreamer-based audio broadcasts**.  
Provides `/start`, `/stop`, and `/status` endpoints to control multicast or direct-stream audio pipelines.

---

## 🚀 Features

- RESTful API for starting and stopping GStreamer audio pipelines
- PID-based process control (safe, avoids global `pkill`)
- Logging with timestamps to `/var/log/gstreamer_api.log`
- JSON responses for all endpoints
- Compatible with systemd or Docker deployment

---

## ⚙️ Requirements

### System Packages

```bash
sudo apt update
sudo apt install -y python3 python3-pip \
    gstreamer1.0-tools \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly
````

### Python Dependencies

```bash
pip install -r requirements.txt
```

---

## 🧠 API Endpoints

### `POST /start`

Starts a new audio stream.

**Request Body (JSON):**

```json
{
  "source": "http://192.168.1.100:9000/train-automation/audios/alert.mp3",
  "multicast_iface": "eno1",
  "multicast_host": "239.193.0.52",
  "multicast_port": 2100,
  "volume": 10.0
}
```

**Response:**

```json
{
  "status": "started",
  "urlAddress": "http://192.168.1.100:9000/train-automation/audios/alert.mp3"
}
```

---

### `POST /stop`

Stops the currently active stream.

**Response:**

```json
{
  "status": "stopped",
  "urlAddress": "http://192.168.1.100:9000/train-automation/audios/alert.mp3"
}
```

If there’s no active stream:

```json
{
  "status": "no-active-stream",
  "urlAddress": null
}
```

---

### `GET /status`

Checks if a stream is currently active.

**Response (playing):**

```json
{
  "status": "playing",
  "urlAddress": "http://192.168.1.100:9000/train-automation/audios/alert.mp3"
}
```

**Response (idle):**

```json
{
  "status": "idle",
  "urlAddress": null
}
```

---

## 🧾 Example Usage (via curl)

```bash
# Start a stream
curl -X POST http://localhost:8081/start \
  -H "Content-Type: application/json" \
  -d '{"source":"http://192.168.1.100:9000/train-automation/audios/test.mp3"}'

# Check status
curl http://localhost:8081/status

# Stop the stream
curl -X POST http://localhost:8081/stop
```

---

## 🪵 Logs

All activity is logged at:

```
/var/log/gstreamer_api.log
```

Typical entries:

```
2025-10-13 14:10:21 [INFO] Starting stream: gst-launch-1.0 souphttpsrc ...
2025-10-13 14:10:22 [INFO] GStreamer process started (PID=1810)
2025-10-13 14:12:08 [INFO] Stopped GStreamer process (PID=1810)
```

---

## 🧰 Run Manually

```bash

python3 app.py

```

Then open:

➡️ `http://localhost:8081/status`

---

## ⚙️ Optional: Run as a Systemd Service

Create a service file at `/etc/systemd/system/audio-broadcast.service`:

```ini
[Unit]
Description=RRAS Audio Broadcast API
After=network.target

[Service]
ExecStart=/usr/bin/python3 /opt/audio-broadcast-api/app.py
WorkingDirectory=/opt/audio-broadcast-api
Restart=always
User=root
StandardOutput=file:/var/log/gstreamer_api.log
StandardError=file:/var/log/gstreamer_api.log

[Install]
WantedBy=multi-user.target
```

Then enable and start it:

```bash
sudo systemctl daemon-reload
sudo systemctl enable audio-broadcast.service
sudo systemctl start audio-broadcast.service
```

---

## ✅ Health Check

```bash
curl http://localhost:8081/
```

**Response:**

```json
{
  "service": "RRAS Audio Broadcast API",
  "version": "1.2"
}
```

---

## 📜 License

This project is licensed under the [MIT License](LICENSE). See the license file for details.

---

## 🙌 Issues, Feature Requests or Support

Please use the Issue > New Issue button to submit issues, feature requests or support issues directly to me. You can also send an e-mail to akin.bicer@outlook.com.tr.
