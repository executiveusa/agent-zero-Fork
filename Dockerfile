# Multi-stage build for Agent Zero (Next.js Dashboard)
FROM node:20-alpine AS builder

WORKDIR /app

# Copy monorepo package files
COPY package*.json ./
COPY tsconfig.json ./

# Copy vercel-dashboard app files (the main Next.js app to containerize)
COPY apps/vercel-dashboard/package*.json ./apps/vercel-dashboard/
COPY apps/vercel-dashboard/tsconfig.json ./apps/vercel-dashboard/
COPY apps/vercel-dashboard/next.config.js ./apps/vercel-dashboard/
COPY apps/vercel-dashboard/tailwind.config.ts ./apps/vercel-dashboard/
COPY apps/vercel-dashboard/postcss.config.js ./apps/vercel-dashboard/
COPY apps/vercel-dashboard/src ./apps/vercel-dashboard/src
COPY apps/vercel-dashboard/public ./apps/vercel-dashboard/public

# Install dependencies from monorepo root
RUN npm ci

# Build application from dashboard directory
WORKDIR /app/apps/vercel-dashboard
RUN npm ci && npm run build

# Production image
FROM node:20-alpine

WORKDIR /app/apps/vercel-dashboard

# Install dumb-init for proper signal handling
RUN apk add --no-cache dumb-init

# Copy package files from dashboard
COPY apps/vercel-dashboard/package*.json ./

# Install production dependencies only
RUN npm ci --production

# Copy built app from builder
COPY --from=builder /app/apps/vercel-dashboard/.next ./.next
COPY --from=builder /app/apps/vercel-dashboard/public ./public

# Create non-root user for security
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nextjs -u 1001

USER nextjs

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD node -e "require('http').get('http://localhost:3000', (r) => {if (r.statusCode !== 200) throw new Error(r.statusCode)})"

# Use dumb-init to handle signals properly
ENTRYPOINT ["dumb-init", "--"]

# Start application
CMD ["npm", "start"]
