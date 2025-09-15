-- AI Cash Revolution Database Initialization Script
-- Production-ready PostgreSQL setup with security and performance optimizations

-- Create database extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Create custom types
CREATE TYPE user_role AS ENUM ('free', 'premium', 'professional', 'admin');
CREATE TYPE signal_direction AS ENUM ('buy', 'sell', 'hold');
CREATE TYPE signal_status AS ENUM ('pending', 'active', 'closed', 'cancelled');
CREATE TYPE subscription_status AS ENUM ('active', 'cancelled', 'past_due', 'unpaid');

-- Create indexes for performance
-- Will be created automatically by Prisma migrations, but included for reference

-- Performance tuning settings
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;
ALTER SYSTEM SET random_page_cost = 1.1;
ALTER SYSTEM SET effective_io_concurrency = 200;

-- Security settings
ALTER SYSTEM SET log_statement = 'ddl';
ALTER SYSTEM SET log_min_duration_statement = 1000;
ALTER SYSTEM SET log_connections = on;
ALTER SYSTEM SET log_disconnections = on;
ALTER SYSTEM SET log_checkpoints = on;
ALTER SYSTEM SET log_lock_waits = on;

-- Create monitoring views
CREATE OR REPLACE VIEW v_database_stats AS
SELECT
    schemaname,
    tablename,
    attname,
    n_distinct,
    correlation
FROM pg_stats
WHERE schemaname = 'public';

CREATE OR REPLACE VIEW v_slow_queries AS
SELECT
    query,
    calls,
    total_time,
    mean_time,
    rows
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;

-- Create backup user (for automated backups)
CREATE USER backup_user WITH PASSWORD 'backup_secure_password_change_me';
GRANT CONNECT ON DATABASE aicash_revolution TO backup_user;
GRANT USAGE ON SCHEMA public TO backup_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO backup_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO backup_user;

-- Create monitoring user (for metrics collection)
CREATE USER monitoring_user WITH PASSWORD 'monitoring_secure_password_change_me';
GRANT CONNECT ON DATABASE aicash_revolution TO monitoring_user;
GRANT pg_monitor TO monitoring_user;

-- Application user (will be created by Prisma)
-- CREATE USER aicash_user WITH PASSWORD 'secure_app_password_change_me';
-- GRANT CONNECT ON DATABASE aicash_revolution TO aicash_user;
-- GRANT USAGE, CREATE ON SCHEMA public TO aicash_user;
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO aicash_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO aicash_user;

-- Reload configuration
SELECT pg_reload_conf();