# Stage 1: 构建 Vue 应用
FROM node:18-alpine AS build
WORKDIR /app
COPY frontend/package*.json ./
# 使用缓存挂载，避免重复下载 node_modules
RUN --mount=type=cache,target=/root/.npm \
    npm ci
COPY frontend/ .
RUN npm run build

# Stage 2: Nginx 服务
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY docker/frontend/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
