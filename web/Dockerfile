# Sahayak web — Next.js standalone.
# Build from the REPO ROOT so /shared is importable:
#   docker build -f web/Dockerfile -t sahayak-web .
FROM node:20-slim AS deps
WORKDIR /repo/web
COPY web/package.json web/package-lock.json* ./
RUN npm install --no-audit --no-fund

FROM node:20-slim AS build
WORKDIR /repo
COPY shared ./shared
COPY web ./web
COPY --from=deps /repo/web/node_modules ./web/node_modules
WORKDIR /repo/web
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

FROM node:20-slim AS run
WORKDIR /app
ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1
# Standalone output bundles only what the server needs.
COPY --from=build /repo/web/.next/standalone ./
COPY --from=build /repo/web/.next/static ./web/.next/static
COPY --from=build /repo/web/public ./web/public
EXPOSE 3000
ENV PORT=3000
CMD ["node", "web/server.js"]
