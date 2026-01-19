# STAGE 1: Assets
FROM alpine:latest AS assets
COPY . /assets

# STAGE 2: Test (Dummy check)
FROM alpine:latest AS tester
COPY --from=assets /assets /assets
RUN test -f /assets/index.html && echo "Index exists"

# STAGE 3: Final
FROM nginx:stable-alpine AS final
# Copy static files
COPY --from=assets /assets /usr/share/nginx/html
# Copy custom Nginx config
COPY --from=assets /assets/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
