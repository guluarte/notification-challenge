FROM node:20-bookworm-slim AS builder

WORKDIR /app

ARG NPM_VERSION=11.6.2

RUN npm install -g npm@$NPM_VERSION

COPY package.json package-lock.json ./

RUN npm ci

COPY . .

RUN npm run build

FROM nginx:1.27-alpine AS runtime

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80
