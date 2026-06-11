FROM python:3.12-slim AS backend

WORKDIR /app/backend

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY backend/ .

RUN mkdir -p uploads stockfish/stockfish \
    && wget -q "https://github.com/official-stockfish/Stockfish/releases/download/sf_17.1/stockfish-ubuntu-x86-64-avx2.tar" -O /tmp/stockfish.tar \
    && tar -xf /tmp/stockfish.tar -C /tmp \
    && mv /tmp/stockfish/stockfish-ubuntu-x86-64-avx2 stockfish/stockfish/stockfish-linux-modern \
    && chmod +x stockfish/stockfish/stockfish-linux-modern \
    && rm -rf /tmp/stockfish* \
    || echo "Stockfish download failed, please provide binary manually"

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "--timeout", "300", "run:app"]


FROM node:18-alpine AS frontend-build

WORKDIR /app/frontend

COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci

COPY frontend/ .
RUN npm run build


FROM nginx:alpine AS production

COPY --from=frontend-build /app/frontend/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
