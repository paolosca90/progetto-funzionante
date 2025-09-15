# AI Cash Revolution Server - Production Dockerfile
# Multi-stage build for optimal production image size and security

# Stage 1: Base dependencies
FROM node:18-alpine AS base
WORKDIR /app

# Install security updates and required packages
RUN apk update && apk upgrade && \
    apk add --no-cache \
    dumb-init \
    curl \
    tzdata \
    && rm -rf /var/cache/apk/*

# Create non-root user for security
RUN addgroup -g 1001 -S nodejs && \
    adduser -S aicash -u 1001

# Stage 2: Dependencies installation
FROM base AS deps
WORKDIR /app

# Copy package files
COPY server/package*.json ./
COPY server/prisma ./prisma/

# Install dependencies with production optimizations
RUN npm ci --only=production --ignore-scripts && \
    npm cache clean --force

# Generate Prisma client
RUN npx prisma generate

# Stage 3: Build stage
FROM base AS build
WORKDIR /app

# Copy package files and source
COPY server/package*.json ./
COPY server/prisma ./prisma/
COPY server/src ./src/
COPY server/tests ./tests/

# Install all dependencies for building
RUN npm ci --ignore-scripts

# Generate Prisma client
RUN npx prisma generate

# Run tests and linting
RUN npm run test
RUN npm run lint

# Build the application (if build script exists)
RUN npm run build || echo "No build script found, skipping..."

# Stage 4: Production runtime
FROM base AS runtime
WORKDIR /app

# Copy dependencies from deps stage
COPY --from=deps --chown=aicash:nodejs /app/node_modules ./node_modules
COPY --from=deps --chown=aicash:nodejs /app/prisma ./prisma

# Copy application code
COPY --chown=aicash:nodejs server/src ./src
COPY --chown=aicash:nodejs server/package*.json ./

# Create logs directory
RUN mkdir -p /app/logs && chown aicash:nodejs /app/logs

# Set environment variables
ENV NODE_ENV=production
ENV PORT=3000
ENV LOG_LEVEL=info

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:3000/api/health || exit 1

# Expose port
EXPOSE 3000

# Switch to non-root user
USER aicash

# Use dumb-init to handle signals properly
ENTRYPOINT ["dumb-init", "--"]

# Start the application
CMD ["node", "src/app.js"]