#!/bin/sh
cd /app

# Run migrations at startup (env vars available now)
alembic upgrade head

# Start backend on port 8001
uvicorn app.main:app --host 127.0.0.1 --port 8001 &
BACKEND_PID=$!

# Start nginx on port 8000
nginx -g "daemon off;" &
NGINX_PID=$!

wait $BACKEND_PID $NGINX_PID
