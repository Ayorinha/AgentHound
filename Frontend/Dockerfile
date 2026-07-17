# AgentHound frontend container (Next.js, standalone output).

FROM node:22-alpine AS base
RUN corepack enable

# ---- deps: install dependencies with pnpm, cached separately from source ----
FROM base AS deps
WORKDIR /srv
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml .npmrc ./
RUN pnpm install --frozen-lockfile

# ---- builder: compile the Next.js app ----
FROM base AS builder
WORKDIR /srv
COPY --from=deps /srv/node_modules ./node_modules
COPY . .

# NEXT_PUBLIC_* vars are inlined into the client bundle at build time, so they
# must be supplied as a build ARG (not just a runtime env var on the
# container). Defaults to the backend's compose service, reachable from the
# browser via the host's published port.
ARG NEXT_PUBLIC_AGENTHOUND_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_AGENTHOUND_API_URL=${NEXT_PUBLIC_AGENTHOUND_API_URL}
ENV NEXT_TELEMETRY_DISABLED=1

RUN pnpm build

# ---- runner: minimal runtime image using the Next.js standalone output ----
FROM base AS runner
WORKDIR /srv

ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000 \
    HOSTNAME=0.0.0.0

RUN addgroup --system --gid 1001 nodejs \
    && adduser --system --uid 1001 nextjs

COPY --from=builder /srv/public ./public
COPY --from=builder --chown=nextjs:nodejs /srv/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /srv/.next/static ./.next/static

USER nextjs
EXPOSE 3000

CMD ["node", "server.js"]
