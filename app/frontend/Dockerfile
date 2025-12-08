# Build stage
FROM node:20-alpine as build

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci

# Copy source files
COPY . .

# Fix permissions for node_modules binaries
RUN chmod -R +x node_modules/.bin

# Build the application (outputs to ./dist)
RUN npm run build

# Verify build succeeded
RUN ls -la ./dist && \
    test -f ./dist/index.html || (echo "Build failed: index.html not found" && exit 1)

# Production stage
FROM nginx:alpine

# Install gettext for envsubst
RUN apk add --no-cache gettext

# Copy built files from the build stage
# The build outputs to ./dist relative to /app
COPY --from=build /app/dist /usr/share/nginx/html

# Copy nginx configuration template
COPY nginx.conf /etc/nginx/templates/default.conf.template

# Copy custom entrypoint script
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Cloud Run requires port 8080
EXPOSE 8080

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://localhost:8080/ || exit 1

ENTRYPOINT ["/docker-entrypoint.sh"]