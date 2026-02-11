"""
Dockerfile Generator — Framework-specific templates
====================================================
Generates production Dockerfiles based on detected project type.
All templates include HEALTHCHECK and bind to 0.0.0.0.
"""

TEMPLATES: dict[str, str] = {
    # ── Next.js / React ──────────────────────────────────────
    "nextjs": """\
FROM node:22-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:22-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/package*.json ./
COPY --from=builder /app/node_modules ./node_modules
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \\
  CMD wget -qO- http://localhost:3000/ || exit 1
CMD ["npm", "start"]
""",

    # ── Flask ────────────────────────────────────────────────
    "flask": """\
FROM python:3.13-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends curl \\
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn
COPY . .
ENV FLASK_HOST=0.0.0.0
EXPOSE 5000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \\
  CMD curl -f http://localhost:5000/health || exit 1
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "app:app"]
""",

    # ── Django ───────────────────────────────────────────────
    "django": """\
FROM python:3.13-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends curl \\
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn
COPY . .
ENV DJANGO_SETTINGS_MODULE=config.settings.production
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \\
  CMD curl -f http://localhost:8000/health/ || exit 1
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "config.wsgi:application"]
""",

    # ── FastAPI ──────────────────────────────────────────────
    "fastapi": """\
FROM python:3.13-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends curl \\
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt uvicorn
COPY . .
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \\
  CMD curl -f http://localhost:8000/health || exit 1
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
""",

    # ── Express / Node.js ────────────────────────────────────
    "express": """\
FROM node:22-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --production
COPY . .
ENV HOST=0.0.0.0
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \\
  CMD wget -qO- http://localhost:3000/health || exit 1
CMD ["node", "server.js"]
""",

    "node": """\
FROM node:22-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --production
COPY . .
ENV HOST=0.0.0.0
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \\
  CMD wget -qO- http://localhost:3000/ || exit 1
CMD ["npm", "start"]
""",

    # ── Nuxt ─────────────────────────────────────────────────
    "nuxt": """\
FROM node:22-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:22-alpine AS runner
WORKDIR /app
COPY --from=builder /app/.output ./.output
ENV HOST=0.0.0.0
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \\
  CMD wget -qO- http://localhost:3000/ || exit 1
CMD ["node", ".output/server/index.mjs"]
""",

    # ── Static (nginx) ───────────────────────────────────────
    "static": """\
FROM nginx:alpine
RUN rm /etc/nginx/conf.d/default.conf
COPY . /usr/share/nginx/html/
RUN printf 'server {\\n\\
    listen 80;\\n\\
    server_name _;\\n\\
    root /usr/share/nginx/html;\\n\\
    index index.html;\\n\\
    location / {\\n\\
        try_files $uri $uri/ /index.html;\\n\\
    }\\n\\
    location /health {\\n\\
        access_log off;\\n\\
        return 200 "ok";\\n\\
        add_header Content-Type text/plain;\\n\\
    }\\n\\
}\\n' > /etc/nginx/conf.d/default.conf
EXPOSE 80
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \\
  CMD wget -qO- http://localhost:80/health || exit 1
""",

    # ── Rust ─────────────────────────────────────────────────
    "rust": """\
FROM rust:1.79-alpine AS builder
WORKDIR /app
RUN apk add --no-cache musl-dev
COPY . .
RUN cargo build --release

FROM alpine:3.19
WORKDIR /app
COPY --from=builder /app/target/release/app ./app
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \\
  CMD wget -qO- http://localhost:8080/health || exit 1
CMD ["./app"]
""",

    # ── Go ───────────────────────────────────────────────────
    "go": """\
FROM golang:1.22-alpine AS builder
WORKDIR /app
COPY go.* ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 go build -o server .

FROM alpine:3.19
WORKDIR /app
COPY --from=builder /app/server ./server
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \\
  CMD wget -qO- http://localhost:8080/health || exit 1
CMD ["./server"]
""",

    # ── Python generic ───────────────────────────────────────
    "python": """\
FROM python:3.13-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends curl \\
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \\
  CMD curl -f http://localhost:5000/health || exit 1
CMD ["python", "app.py"]
""",
}


def generate_dockerfile(project_type: str, port: int | None = None) -> str:
    """Generate a Dockerfile for the given project type.

    Args:
        project_type: One of the keys in TEMPLATES
        port: Optional port override (replaces default EXPOSE/port in template)

    Returns:
        Dockerfile content as a string
    """
    template = TEMPLATES.get(project_type, TEMPLATES["node"])

    if port is not None:
        # Replace the EXPOSE line with the correct port
        default_ports = {
            "nextjs": 3000, "flask": 5000, "django": 8000, "fastapi": 8000,
            "express": 3000, "node": 3000, "nuxt": 3000, "static": 80,
            "rust": 8080, "go": 8080, "python": 5000,
        }
        default = default_ports.get(project_type, 3000)
        if port != default:
            template = template.replace(f"EXPOSE {default}", f"EXPOSE {port}")
            template = template.replace(f":{default}", f":{port}")

    return template


def get_supported_types() -> list[str]:
    """Return list of supported project types."""
    return list(TEMPLATES.keys())
