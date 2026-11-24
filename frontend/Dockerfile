FROM node:22-alpine@sha256:0a7108bf6c7bf5de370ffb1a3ed6be93d405b43ff159f681a8d18c0e2bc2e402 AS dependencies

WORKDIR /app

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

FROM dependencies AS development

COPY frontend/index.html frontend/tsconfig.json frontend/vite.config.ts ./
COPY frontend/src ./src

EXPOSE 5173

CMD ["npm", "run", "serve", "--", "--host", "0.0.0.0"]

FROM dependencies AS build

COPY frontend/index.html frontend/tsconfig.json frontend/vite.config.ts ./
COPY frontend/src ./src
RUN npm run build

FROM nginx:1.27-alpine@sha256:65645c7bb6a0661892a8b03b89d0743208a18dd2f3f17a54ef4b76fb8e2f2a10 AS production

# openssl powers the Nginx entrypoint's route-prefix HMAC. Pin a security floor
# rather than an exact revision: Alpine rolls the package revision (-r1 -> -r2 ...)
# within a release, which made an exact `=3.3.7-r1` pin uninstallable and broke CI.
RUN apk add --no-cache "openssl>=3.3.7-r1"
COPY nginx/templates/ /etc/nginx/templates/
COPY nginx/docker-entrypoint.d/ /docker-entrypoint.d/
RUN chmod +x /docker-entrypoint.d/15-phishgate-runtime.envsh
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
