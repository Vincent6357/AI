#!/bin/sh
set -e

# Check if BACKEND_URL is set
if [ -z "$BACKEND_URL" ]; then
    echo "ERROR: BACKEND_URL environment variable is not set!"
    echo "Please set BACKEND_URL to your backend Cloud Run service URL"
    exit 1
fi

echo "Configuring nginx with BACKEND_URL: $BACKEND_URL"

# Process the nginx template
envsubst '${BACKEND_URL}' < /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf

echo "Nginx configuration:"
cat /etc/nginx/conf.d/default.conf

# Test nginx configuration
nginx -t

# Start nginx
exec nginx -g "daemon off;"
