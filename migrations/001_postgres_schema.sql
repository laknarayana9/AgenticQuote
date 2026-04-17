-- Postgres Schema Migration for Phase B
-- This file defines the Postgres database schema for the Agentic HO3 Underwriting Studio

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- Core Tables (Phase A)
-- ============================================================================

-- Run Records - store workflow execution runs
CREATE TABLE IF NOT EXISTS runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_id VARCHAR(255) UNIQUE NOT NULL,
    quote_id VARCHAR(255),
    status VARCHAR(50) NOT NULL DEFAULT 'processing',
    submission_json JSONB NOT NULL,
    workflow_state_json JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_runs_run_id (run_id),
    INDEX idx_runs_status (status),
    INDEX idx_runs_created_at (created_at)
);

-- Human Review Records - store HITL tasks
CREATE TABLE IF NOT EXISTS human_reviews (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_id VARCHAR(255) NOT NULL REFERENCES runs(run_id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    reviewer_id VARCHAR(255),
    review_notes TEXT,
    decision VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    INDEX idx_human_reviews_run_id (run_id),
    INDEX idx_human_reviews_status (status)
);

-- Quote Records - store quote data
CREATE TABLE IF NOT EXISTS quotes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_id VARCHAR(255) UNIQUE NOT NULL REFERENCES runs(run_id) ON DELETE CASCADE,
    quote_id VARCHAR(255) UNIQUE NOT NULL,
    applicant_name VARCHAR(255) NOT NULL,
    address TEXT NOT NULL,
    coverage_amount DECIMAL(15,2),
    premium_amount DECIMAL(15,2),
    decision VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_quotes_run_id (run_id),
    INDEX idx_quotes_quote_id (quote_id)
);

-- ============================================================================
-- Phase A Tables
-- ============================================================================

-- Idempotency Keys - prevent duplicate submissions
CREATE TABLE IF NOT EXISTS idempotency_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    idempotency_key VARCHAR(255) UNIQUE NOT NULL,
    user_id VARCHAR(255),
    request_hash VARCHAR(255),
    response_run_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,
    INDEX idx_idempotency_keys_key (idempotency_key),
    INDEX idx_idempotency_keys_expires (expires_at)
);

-- Tool Calls - track tool invocations
CREATE TABLE IF NOT EXISTS tool_calls (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_id VARCHAR(255) NOT NULL REFERENCES runs(run_id) ON DELETE CASCADE,
    tool_name VARCHAR(255) NOT NULL,
    tool_version VARCHAR(50),
    input_json JSONB,
    output_json JSONB,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    error_message TEXT,
    duration_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    INDEX idx_tool_calls_run_id (run_id),
    INDEX idx_tool_calls_tool_name (tool_name),
    INDEX idx_tool_calls_status (status)
);

-- Retrieval Events - track RAG retrieval operations
CREATE TABLE IF NOT EXISTS retrieval_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_id VARCHAR(255) NOT NULL REFERENCES runs(run_id) ON DELETE CASCADE,
    query TEXT NOT NULL,
    retrieval_plan JSONB,
    result_chunks JSONB,
    hit_count INTEGER,
    latency_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_retrieval_events_run_id (run_id),
    INDEX idx_retrieval_events_created_at (created_at)
);

-- HITL Tasks - human-in-the-loop workflow tasks
CREATE TABLE IF NOT EXISTS hitl_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_id VARCHAR(255) NOT NULL REFERENCES runs(run_id) ON DELETE CASCADE,
    task_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    assigned_to VARCHAR(255),
    task_data JSONB,
    actions JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    INDEX idx_hitl_tasks_run_id (run_id),
    INDEX idx_hitl_tasks_status (status),
    INDEX idx_hitl_tasks_assigned_to (assigned_to)
);

-- ============================================================================
-- Phase B Tables (Enhanced Features)
-- ============================================================================

-- External Provider Logs - track real provider API calls
CREATE TABLE IF NOT EXISTS provider_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_id VARCHAR(255) REFERENCES runs(run_id) ON DELETE SET NULL,
    provider_name VARCHAR(100) NOT NULL,
    provider_type VARCHAR(50) NOT NULL, -- 'geocoding', 'property_profile', 'hazard', 'claims'
    request_json JSONB,
    response_json JSONB,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    status_code INTEGER,
    error_message TEXT,
    duration_ms INTEGER,
    cost_usd DECIMAL(10,4),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_provider_logs_run_id (run_id),
    INDEX idx_provider_logs_provider_name (provider_name),
    INDEX idx_provider_logs_provider_type (provider_type),
    INDEX idx_provider_logs_created_at (created_at)
);

-- Cache - store cached provider responses
CREATE TABLE IF NOT EXISTS cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cache_key VARCHAR(500) UNIQUE NOT NULL,
    cache_value JSONB NOT NULL,
    provider_name VARCHAR(100),
    ttl_seconds INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,
    hit_count INTEGER DEFAULT 0,
    INDEX idx_cache_key (cache_key),
    INDEX idx_cache_expires (expires_at)
);

-- Audit Trail - track all significant state changes
CREATE TABLE IF NOT EXISTS audit_trail (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_id VARCHAR(255) REFERENCES runs(run_id) ON DELETE SET NULL,
    entity_type VARCHAR(100) NOT NULL,
    entity_id VARCHAR(255),
    action VARCHAR(100) NOT NULL,
    old_value JSONB,
    new_value JSONB,
    user_id VARCHAR(255),
    ip_address VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_audit_trail_run_id (run_id),
    INDEX idx_audit_trail_entity_type (entity_type),
    INDEX idx_audit_trail_created_at (created_at)
);

-- Performance Metrics - store workflow performance data
CREATE TABLE IF NOT EXISTS performance_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_id VARCHAR(255) REFERENCES runs(run_id) ON DELETE SET NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(15,4),
    metric_unit VARCHAR(50),
    tags JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_performance_metrics_run_id (run_id),
    INDEX idx_performance_metrics_metric_name (metric_name),
    INDEX idx_performance_metrics_created_at (created_at)
);

-- ============================================================================
-- Functions and Triggers
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for updated_at
CREATE TRIGGER update_runs_updated_at BEFORE UPDATE ON runs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_hitl_tasks_updated_at BEFORE UPDATE ON hitl_tasks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- Views
-- ============================================================================

-- View for active runs
CREATE OR REPLACE VIEW active_runs AS
SELECT id, run_id, quote_id, status, created_at
FROM runs
WHERE status IN ('processing', 'waiting_for_info', 'pending_review');

-- View for recent provider logs
CREATE OR REPLACE VIEW recent_provider_logs AS
SELECT id, run_id, provider_name, provider_type, status, duration_ms, created_at
FROM provider_logs
WHERE created_at > CURRENT_TIMESTAMP - INTERVAL '24 hours'
ORDER BY created_at DESC;

-- ============================================================================
-- Initial Data
-- ============================================================================

-- No initial data required for Phase B
