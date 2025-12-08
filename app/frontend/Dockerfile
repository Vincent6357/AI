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

# Build the application (outputs to ../backend/static)
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built files from the build stage
# The build outputs to ../backend/static relative to /app
# So from Docker's perspective it's at /backend/static
COPY --from=build /backend/static /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Cloud Run requires port 8080
EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]