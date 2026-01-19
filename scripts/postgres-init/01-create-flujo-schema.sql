-- Create flujo schema for AI orchestration state
CREATE SCHEMA IF NOT EXISTS flujo;

-- Enable pgvector extension for Flujo vector store migrations
CREATE EXTENSION IF NOT EXISTS vector;

-- Grant permissions for the current user
GRANT ALL PRIVILEGES ON SCHEMA flujo TO CURRENT_USER;
