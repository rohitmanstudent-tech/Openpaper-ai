# ── Build stage ──────────────────────────────
FROM node:26-alpine AS builder

WORKDIR /build

# Copy root workspace config + lockfile (layer caching)
COPY package.json package-lock.json ./

# Copy workspace package.json files (layer caching for npm ci)
COPY apps/web/package.json apps/web/package.json
COPY packages/shared/package.json packages/shared/package.json

# Install all workspace dependencies (hoisted to /build/node_modules)
RUN npm ci

# Copy source code
COPY apps/web/ ./apps/web/
COPY packages/shared/ ./packages/shared/

# Build only the web workspace
RUN npm run build --workspace=apps/web

# ── Production stage ─────────────────────────
FROM node:26-alpine AS runner

RUN addgroup -S openpaper && adduser -S openpaper -G openpaper

WORKDIR /app

ENV NODE_ENV=production

ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

COPY --from=builder /build/apps/web/.next ./.next
COPY --from=builder /build/apps/web/public ./public
COPY --from=builder /build/apps/web/package.json ./package.json
COPY --from=builder /build/node_modules ./node_modules

USER openpaper

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:3000/ || exit 1

CMD ["npm", "start"]
