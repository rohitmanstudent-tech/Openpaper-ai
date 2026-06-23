# ── Build stage ──────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /build

COPY package.json tsconfig.json next.config.js postcss.config.js tailwind.config.js ./
COPY src/ ./src/
COPY public/ ./public/

RUN npm ci && npm run build

# ── Production stage ─────────────────────────
FROM node:20-alpine AS runner

RUN addgroup -S openpaper && adduser -S openpaper -G openpaper

WORKDIR /app

ENV NODE_ENV=production

COPY --from=builder /build/.next ./.next
COPY --from=builder /build/public ./public
COPY --from=builder /build/package.json ./package.json
COPY --from=builder /build/node_modules ./node_modules

USER openpaper

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:3000/api/health || exit 1

CMD ["npm", "start"]
