# --- STAGE 1: Build React App ---
FROM node:20-alpine AS build

WORKDIR /app

# 1. Copy package.json
COPY frontend/package*.json ./
RUN npm ci

# 2. Copy source code AND the .env file
# (Since your .env is inside 'frontend/', this copies it to /app/.env)
COPY frontend/ .

# 3. Build (Vite will read the .env file automatically)
ENV NODE_OPTIONS="--max-old-space-size=4096"
RUN npm run build

# --- STAGE 2: Nginx Server ---
FROM nginx:alpine

# Copy Nginx config
COPY nginx/nginx.conf /etc/nginx/conf.d/default.conf

# Copy built assets
COPY --from=build /app/dist /usr/share/nginx/html

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]