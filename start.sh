#!/bin/sh
cd /app

# Start backend on port 8001
uvicorn app.main:app --host 127.0.0.1 --port 8001 &
BACKEND_PID=$!

# Start nginx on port 8000 (Railway exposes this)
nginx -g "daemon off;" &
NGINX_PID=$!

wait $BACKEND_PID $NGINX_PID
