FROM nginx:alpine AS builder

WORKDIR /myapp

COPY static ./static

COPY templates ./templates


RUN mkdir -p /myapp/client \
    && cp templates/index.html /myapp/client/index.html \
    && cp -r static /myapp/client/static

FROM nginxinc/nginx-unprivileged:1.30-alpine

COPY --from=builder /myapp/client/ /usr/share/nginx/html/

EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]