FROM nginx:alpine

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Copy custom nginx configuration listening on port 3000
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy static frontend assets
COPY . /usr/share/nginx/html

# Expose frontend port
EXPOSE 3000

CMD ["nginx", "-g", "daemon off;"]
