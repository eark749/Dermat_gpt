-- Initialize DermaGPT Database
-- This script runs when PostgreSQL container starts for the first time

-- Create database if it doesn't exist (handled by POSTGRES_DB env var)
-- CREATE DATABASE dermagpt;

-- Create user if it doesn't exist (handled by POSTGRES_USER env var)
-- CREATE USER dermagpt_user WITH PASSWORD 'dermagpt_password';

-- Grant privileges
-- GRANT ALL PRIVILEGES ON DATABASE dermagpt TO dermagpt_user;

-- Switch to the application database
\c dermagpt;

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- The actual tables will be created by Alembic migrations
-- This file is just for initial setup and extensions
