# =============================================================================
# ResearchMind AI — Frontend Dockerfile
# =============================================================================
# Multi-stage build:
#   1. deps     — Install dependencies (cached layer)
#   2. build    — Next.js production build
#   3. runner   — Minimal production image
# =============================================================================

# ---------------------------------------------------------------------------
# Stage 1 — Dependencies
# ---------------------------------------------------------------------------
FROM node:22-alpine AS deps

WORKDIR /app

COPY package.json package-lock.json* ./
# Install ALL dependencies (including devDependencies) — they are needed for
# the Next.js build (PostCSS, Tailwind, lightningcss, etc.). The runner stage
# only copies the standalone output, which is self-contained.
RUN npm ci --prefer-offline

# ---------------------------------------------------------------------------
# Stage 2 — Build
# ---------------------------------------------------------------------------
FROM node:22-alpine AS build

WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Build the Next.js application
RUN npm run build

# ---------------------------------------------------------------------------
# Stage 3 — Production runner
# ---------------------------------------------------------------------------
FROM node:22-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1

# Copy only what's needed for production
COPY --from=build /app/public ./public
COPY --from=build /app/.next/standalone ./
COPY --from=build /app/.next/static ./.next/static

# Expose the application port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000/health || exit 1

# Start the Next.js standalone server
CMD ["node", "server.js"]
