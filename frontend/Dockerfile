# =============================================================================
# Student Success Predictor — Frontend Production Image
# =============================================================================
# Multi-stage: build the static SPA with Node, serve it with Nginx which also
# reverse-proxies /api to the backend container (single-origin deployment).
#
# Build:
#   docker build -f frontend/Dockerfile -t student-predictor-frontend .
# =============================================================================

# ---- Stage 1: build ---------------------------------------------------------
FROM node:24-alpine AS build

WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund

COPY frontend/tsconfig.json frontend/vite.config.ts frontend/index.html ./
COPY frontend/src ./src
RUN npm run build

# ---- Stage 2: serve ---------------------------------------------------------
FROM nginx:1.27-alpine

COPY deployment/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /build/dist /usr/share/nginx/html

EXPOSE 80
# The container health probe (wget ships with alpine nginx images).
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -q -O /dev/null http://localhost/ || exit 1