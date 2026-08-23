FROM node:20-alpine AS frontend-build
WORKDIR /app
RUN npm install -g pnpm@10.11.0
COPY frontend/package.json frontend/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY frontend/ .
RUN pnpm run build

FROM python:3.12-slim
WORKDIR /app

RUN apt-get update && apt-get install -y nginx && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

COPY --from=frontend-build /app/dist /app/frontend-dist
COPY nginx-railway.conf /etc/nginx/sites-available/default
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

EXPOSE 8000
CMD ["sh", "start.sh"]
