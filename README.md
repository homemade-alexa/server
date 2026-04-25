# Homemade Alexa Server

FastAPI backend for a voice assistant system based on ESP32S3-Box-3. Handles two types of clients: ESP32 devices (local network) and a webapp (public access via reverse proxy).

## Running

```bash
pip install -r requirements.txt
python src/server.py
```

The server starts on the `host`/`port` from `config.toml` (default: `0.0.0.0:8080`).

## Configuration (`config.toml`)

```toml
[server]
host = "0.0.0.0"
port = 8080
serve_url = "http://YOUR_SERVER_IP:8080"   # URL visible to ESP32 devices (OTA download)

[firmware]
dir = "./firmware"

[audio]
log_dir = "./audio_log"
save_audio = false

[audio_server]
url = "http://YOUR_AUDIO_SERVER_IP:1234"   # server that plays WAV via aplay

[auth]
password_hash = ""   # bcrypt: python -c "from src.helpers.Auth import hash_password; print(hash_password('yourpassword'))"
jwt_secret    = ""   # random: python -c "import secrets; print(secrets.token_hex(32))"
jwt_expire_days = 30

[openai]
api_key = "..."
model   = "gpt-4.1"
session_timeout_seconds = 300
```

## Architecture

```
                   ┌─────────────┐
                   │   Apache    │  (public reverse proxy)
                   │  your.domain│
                   └──────┬──────┘
          /api/public/*   │   /ws/public
                          │
                   ┌──────▼──────┐
     ESP32 ────WS /ws────►       │
     ESP32 ──POST /api/internal/stt──► Alexa Server :8080
                   │   FastAPI   │
                   └──────┬──────┘
                          │
              ┌───────────┼────────────┐
              ▼           ▼            ▼
         OpenAI STT   Azure TTS   Audio Server :1234
```

## Client flows

### ESP32 (local network)

1. Device connects over WebSocket `/ws/internal` and sends `{"hello": {"hostname": "...", "hw_type": "..."}}` — registers in `DeviceRegistry` under its IP.
2. After wake word detection, sends `{"event": "wakeword"}` — server interrupts current audio playback.
3. Device sends PCM audio to `POST /api/internal/stt`.
4. Server transcribes speech (STT), interprets the command via LLM, generates a TTS response.
5. Response audio is sent to Audio Server (`POST /api/play`), which plays it through the speaker.
6. After playback ends, server sends over WS either `{"cmd": "listen"}` (continue conversation) or `{"cmd": "idle"}` (end).

### Webapp (via Apache)

1. Webapp connects over WebSocket `/ws/public?token=<jwt>` — token verified at handshake (code 4001 on error).
2. Webapp registers in `DeviceRegistry` the same way as ESP32 (same data structures).
3. User records audio in the browser and sends it to `POST /api/public/stt` with header `Authorization: Bearer <token>`.
4. Server transcribes speech, interprets the command, generates TTS, and returns the audio base64-encoded directly in the JSON response.
5. Webapp plays audio locally via Web Audio API.
6. The `next` field in the response (`"listen"` or `"idle"`) determines whether the webapp automatically starts the next recording.

## Endpoints

### Public — requires JWT (`Authorization: Bearer <token>`)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/public/stt` | PCM audio → STT → LLM → TTS; returns `{status, command, next, audio_b64}` |
| `WS`   | `/ws/public?token=<jwt>` | WebSocket for webapp; token verified at handshake |

### Public — no auth

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/public/auth/login` | `{password}` → `{token}`; returns JWT on correct password |

### Internal — no auth (not exposed via reverse proxy)

| Method | Path | Description |
|--------|------|-------------|
| `WS`   | `/ws/internal` | WebSocket for ESP32 devices |
| `POST` | `/api/internal/stt` | PCM audio from ESP32 → STT → LLM → TTS → Audio Server; responds immediately, processing in background |
| `POST` | `/api/internal/abort` | Interrupts current playback via Audio Server |
| `POST` | `/api/internal/listen` | Sends `{"cmd":"listen"}` to all connected devices |
| `POST` | `/api/internal/display` | Sends `{"cmd":"display","data":{title,text}}` to all devices |
| `POST` | `/api/internal/ota` | Sends `{"cmd":"ota_start","ota_url":"..."}` with the latest `.bin` from the firmware directory |
| `GET`  | `/api/internal/status` | List of connected devices and firmware files |
| `GET`  | `/firmware/{filename}` | Serves `.bin` files for download by ESP32 during OTA |

### Audio headers (STT endpoints)

| Header | Default | Description |
|--------|---------|-------------|
| `x-audio-codec` | `pcm` | Codec |
| `x-audio-sample-rate` | `16000` | Hz |
| `x-audio-bits` | `16` | Bit depth |
| `x-audio-channel` | `1` | Number of channels |

### WebSocket commands (server → device)

| Command | Description |
|---------|-------------|
| `{"cmd": "listen"}` | Triggers listening mode on the device |
| `{"cmd": "idle"}` | Switches device to idle state |
| `{"cmd": "display", "data": {"title": "...", "text": "..."}}` | Displays text, wakes the screen |
| `{"cmd": "ota_start", "ota_url": "..."}` | Starts OTA; device downloads firmware from the given URL |
| `{"cmd": "restart"}` | Restarts the device |

## Apache2 configuration (reverse proxy)

Required modules: `proxy`, `proxy_http`, `proxy_wstunnel`, `rewrite`, `ssl`.

```apache
<VirtualHost *:80>
    ServerName your.domain
    RewriteEngine On
    RewriteRule ^ https://%{HTTP_HOST}%{REQUEST_URI} [END,NE,R=permanent]
</VirtualHost>

<IfModule mod_ssl.c>
<VirtualHost *:443>
    ServerName your.domain

    # Webapp (static files)
    ProxyPass        /alexa/  http://backend.vpn/alexa/
    ProxyPassReverse /alexa/  http://backend.vpn/alexa/

    # Public API (auth enforced on FastAPI side)
    ProxyPass        /api/public/  http://backend.vpn:8080/api/public/
    ProxyPassReverse /api/public/  http://backend.vpn:8080/api/public/

    # WebSocket for webapp (token in query string)
    RewriteEngine On
    RewriteCond %{HTTP:Upgrade} websocket [NC]
    RewriteRule ^/ws/public$  ws://backend.vpn:8080/ws/public  [P,L]

    SSLCertificateFile    /etc/letsencrypt/live/your.domain/fullchain.pem
    SSLCertificateKeyFile /etc/letsencrypt/live/your.domain/privkey.pem
    Include /etc/letsencrypt/options-ssl-apache.conf

    ErrorLog  /var/log/apache2/alexa-error.log
    CustomLog /var/log/apache2/alexa-access.log combined
</VirtualHost>
</IfModule>
```

Internal endpoints (`/ws/internal`, `/api/internal/*`, `/firmware/*`) intentionally have no proxy entries — accessible only from the local network directly on port 8080.

## Project structure

```
server/
├── config.toml
├── requirements.txt
├── firmware/          # .bin files for OTA
├── audio_log/         # optional WAV logs
└── src/
    ├── server.py
    ├── helpers/
    │   ├── Auth.py            # JWT + bcrypt
    │   ├── AudioClient.py     # POST to audio_server
    │   ├── DeviceRegistry.py  # WebSocket connection registry
    │   ├── ReminderScheduler.py  # APScheduler + SQLite
    │   ├── SpeechToText.py    # Azure / Whisper STT
    │   ├── TTSHelper.py       # Azure TTS (Zofia Neural, pl-PL)
    │   └── WavSaver.py / WavHelper.py
    └── command/
        ├── Interpreter.py     # command dispatch
        ├── LLMRouter.py       # GPT-4.1 tool calling
        ├── IntentModule.py    # module base class
        └── modules/           # Reminder, Weather, Lights, TV, …
```
