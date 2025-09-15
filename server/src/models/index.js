/**
 * Database models and exports
 * Using Prisma client for type-safe database operations
 */

// Export Prisma models directly from the generated client
// This provides type-safe database operations
const { PrismaClient } = require('@prisma/client');

// Create and export the Prisma client instance
const prisma = new PrismaClient();
prisma.$connect().catch((error) => {
  console.error('Failed to connect to database:', error);
  process.exit(1);
});

// Export individual models for convenience (though Prisma handles most operations)
const User = prisma.user;
const UserProfile = prisma.userProfile;
const UserSubscription = prisma.userSubscription;
const TradingInstrument = prisma.tradingInstrument;
const TradingSignal = prisma.tradingSignal;
const SignalExecution = prisma.signalExecution;
const MLAnalysisRun = prisma.mLAnalysisRun;
const MLSignalPerformance = prisma.mLSignalPerformance;
const VolumeAnalysisData = prisma.volumeAnalysisData;
const NewsSentimentData = prisma.newsSentimentData;
const SystemHealth = prisma.systemHealth;
const AuditLog = prisma.auditLog;

// Custom model methods and business logic can be added here

/**
 * User model extensions
 */
User.findActiveByEmail = async function(email) {
  return prisma.user.findFirst({
    where: {
      email: email.toLowerCase(),
      isActive: true,
    },
    include: {
      profiles: true,
      subscription: {
        where: {
          isActive: true,
        },
      },
    },
  });
};

User.findById = function(id) {
  return prisma.user.findUnique({
    where: { id },
    include: {
      profiles: true,
      subscription: true,
    },
  });
};

/**
 * Trading signal model extensions
 */
TradingSignal.findActiveSignals = function(userId, limit = 50) {
  return prisma.tradingSignal.findMany({
    where: {
      userId,
      status: 'active',
      expiresAt: {
        gt: new Date(),
      },
    },
    include: {
      instrument: true,
      executions: true,
    },
    orderBy: {
      generatedAt: 'desc',
    },
    take: limit,
  });
};

TradingSignal.createSignal = async function(signalData) {
  return prisma.$transaction(async (tx) => {
    // Create the signal
    const signal = await tx.tradingSignal.create({
      data: {
        ...signalData,
        signalId: `SIG-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      },
      include: {
        instrument: true,
      },
    });

    // Create audit log entry
    await tx.auditLog.create({
      data: {
        userId: signalData.userId,
        action: 'signal_generated',
        resource: 'trading_signal',
        resourceId: signal.id,
        newValues: signal,
      },
    });

    return signal;
  });
};

/**
 * System health check
 */
SystemHealth.checkService = async function(serviceName) {
  const healthCheck = await prisma.systemHealth.findFirst({
    where: {
      service: serviceName,
      lastCheck: {
        gte: new Date(Date.now() - 5 * 60 * 1000), // Last 5 minutes
      },
    },
    orderBy: {
      lastCheck: 'desc',
    },
  });

  return healthCheck?.status === 'healthy';
};

SystemHealth.updateServiceHealth = async function(serviceName, status, metadata = {}) {
  const nextCheck = new Date(Date.now() + 60 * 1000); // Next check in 1 minute

  return prisma.systemHealth.upsert({
    where: {
      service: serviceName,
      // Note: Prisma doesn't support compound unique constraints for upsert in this way
      // This is a simplified approach - in production, you'd use a composite key if needed
    },
    update: {
      status,
      lastCheck: new Date(),
      nextCheck,
      metadata,
      responseTime: metadata.responseTime || null,
      errorMessage: metadata.error || null,
    },
    create: {
      service: serviceName,
      status,
      lastCheck: new Date(),
      nextCheck,
      metadata,
      responseTime: metadata.responseTime || null,
      errorMessage: metadata.error || null,
    },
  });
};

module.exports = {
  prisma,
  User,
  UserProfile,
  UserSubscription,
  TradingInstrument,
  TradingSignal,
  SignalExecution,
  MLAnalysisRun,
  MLSignalPerformance,
  VolumeAnalysisData,
  NewsSentimentData,
  SystemHealth,
  AuditLog,
};