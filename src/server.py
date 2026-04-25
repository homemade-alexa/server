#!/usr/bin/env python3
import uvicorn
from api.common import HOST, PORT

if __name__ == "__main__":
    uvicorn.run(
        "api:app",
        host=HOST,
        port=PORT,
        log_level="info",
        ws_ping_interval=30,
        ws_ping_timeout=10,
    )
