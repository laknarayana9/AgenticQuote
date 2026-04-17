# Phase B Implementation Plan

## Overview

Phase B focuses on real provider integrations, enhanced agent capabilities with LLMs, and production-grade features while maintaining the mock provider pattern for testing.

## Phase B Goals

1. **Real Provider Integrations** - Replace mock providers with real API integrations (with fallback to mocks)
2. **Enhanced Agent Reasoning** - Integrate LLMs for more sophisticated decision-making
3. **Web Search Integration** - Add external web search for verification
4. **Full HITL Workflow** - Complete human-in-the-loop workflow with actions
5. **Production Scale** - Add caching, Postgres migration, observability

## Implementation Phases

### Phase B.1: Provider Gateway & Real Integrations (Priority: HIGH)

**Objective:** Create a provider gateway that switches between mock and real providers based on configuration.

**Tasks:**
1. Implement `ProviderGateway` class with mock/real switch
2. Implement real Google Maps geocoding provider
3. Implement real property data provider (CoreLogic/ATTOM)
4. Implement real hazard scores provider (FEMA/RiskFactor)
5. Implement real claims history provider (CLUE/LexisNexis)
6. Add provider response caching
7. Add provider error handling and retry logic
8. Add provider metrics (latency, success rate, cost)

**Deliverables:**
- `tools/provider_gateway.py` - Provider gateway with mock/real switch
- `tools/google_geocoding.py` - Real Google Maps provider
- `tools/property_data_provider.py` - Real property data provider
- `tools/hazard_data_provider.py` - Real hazard data provider
- `tools/claims_data_provider.py` - Real claims data provider
- `tools/cache.py` - Provider response caching
- Environment variable configuration
- Provider metrics dashboard

**Acceptance Criteria:**
- Providers switch based on `USE_REAL_PROVIDERS` environment variable
- Mock providers remain default for testing
- Real providers require API keys
- Caching reduces API calls by 80%+
- Error handling with retry logic
- Metrics exported to Phoenix/Arize

### Phase B.2: LLM Integration for Enhanced Agent Reasoning (Priority: HIGH)

**Objective:** Integrate LLMs for enhanced agent reasoning while maintaining determinism.

**Tasks:**
1. Integrate OpenAI API for agent reasoning
2. Update agents to use LLM for decision-making
3. Add LLM prompt templates for each agent
4. Implement LLM response validation
5. Add LLM cost tracking
6. Implement LLM fallback to deterministic logic
7. Add LLM temperature and parameter configuration
8. Test LLM integration with sample scenarios

**Deliverables:**
- `tools/llm_client.py` - LLM client wrapper
- `workflows/agents.py` - Updated agents with LLM integration
- `prompts/` - Agent prompt templates
- LLM configuration in environment variables
- LLM cost tracking
- LLM fallback logic

**Acceptance Criteria:**
- Agents use LLM when `USE_LLM=true`
- Agents fall back to deterministic logic on LLM failure
- LLM responses validated against schemas
- LLM costs tracked and reported
- Temperature ≤ 0.2 for determinism
- All demo scenarios pass with LLM enabled

### Phase B.3: Web Search Integration (Priority: MEDIUM)

**Objective:** Add external web search for verification and additional context.

**Tasks:**
1. Integrate web search API (Tavily, Perplexity, or custom)
2. Add web search to VerifierGuardrailAgent
3. Implement web search result validation
4. Add web search caching
5. Add web search rate limiting
6. Add web search cost tracking
7. Test web search integration

**Deliverables:**
- `tools/web_search.py` - Web search client
- `workflows/agents.py` - Updated verifier with web search
- Web search configuration
- Web search caching
- Web search metrics

**Acceptance Criteria:**
- Web search used when `USE_WEB_SEARCH=true`
- Search results validated for relevance
- Caching reduces search calls by 70%+
- Rate limiting prevents API abuse
- Cost tracking for search API

### Phase B.4: Full HITL Workflow (Priority: MEDIUM)

**Objective:** Complete human-in-the-loop workflow with actions and task management.

**Tasks:**
1. Implement HITL task creation and assignment
2. Implement HITL actions (approve, reject, request info, refer)
3. Implement HITL workflow state management
4. Add HITL UI endpoints
5. Implement HITL notification system
6. Add HITL SLA tracking
7. Implement HITL audit trail
8. Test HITL workflow end-to-end

**Deliverables:**
- `workflows/hitl.py` - HITL workflow orchestration
- `app/api_hitl.py` - HITL API endpoints
- `models/hitl.py` - HITL data models
- HITL UI components
- HITL notification system
- HITL audit trail

**Acceptance Criteria:**
- HITL tasks created automatically
- HITL actions update workflow state
- SLA tracking and alerts
- Full audit trail
- UI for reviewers
- All HITL scenarios tested

### Phase B.5: Production Scale Features (Priority: LOW)

**Objective:** Add production-grade features for scale and reliability.

**Tasks:**
1. Implement Postgres migration from SQLite
2. Add database connection pooling
3. Implement database query optimization
4. Add API rate limiting
5. Implement request queuing (Redis)
6. Add health check endpoints
7. Implement graceful shutdown
8. Add production monitoring

**Deliverables:**
- Postgres migration script
- Database connection pooling
- API rate limiting middleware
- Redis queue integration
- Health check endpoints
- Production monitoring dashboard

**Acceptance Criteria:**
- Postgres migration tested
- Connection pooling configured
- Rate limiting prevents abuse
- Queue handles high load
- Health checks pass
- Monitoring alerts configured

## Implementation Order

### Sprint 1: Provider Gateway & Real Integrations (2 weeks)
- Week 1: Provider gateway, Google Maps geocoding, caching
- Week 2: Property data, hazard scores, claims history providers

### Sprint 2: LLM Integration (1 week)
- LLM client, agent updates, prompt templates, testing

### Sprint 3: Web Search & HITL (2 weeks)
- Week 1: Web search integration
- Week 2: Full HITL workflow

### Sprint 4: Production Scale (1 week)
- Postgres migration, rate limiting, monitoring

## Configuration

### Environment Variables

```bash
# Provider Configuration
USE_REAL_PROVIDERS=false  # Default: false (use mocks)
GOOGLE_MAPS_API_KEY=your_key
PROPERTY_DATA_API_KEY=your_key
HAZARD_DATA_API_KEY=your_key
CLUE_API_KEY=your_key

# LLM Configuration
USE_LLM=false  # Default: false
OPENAI_API_KEY=your_key
LLM_TEMPERATURE=0.2
LLM_MODEL=gpt-4

# Web Search Configuration
USE_WEB_SEARCH=false  # Default: false
WEB_SEARCH_API_KEY=your_key
WEB_SEARCH_PROVIDER=tavily

# Database Configuration
DATABASE_TYPE=sqlite  # Default: sqlite
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=agentic_underwriting
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# Observability
OTLP_ENDPOINT=localhost:4317
PHOENIX_ENDPOINT=http://localhost:6006
```

## Testing Strategy

### Unit Tests
- Provider gateway tests (mock and real)
- LLM client tests
- Web search client tests
- HITL workflow tests

### Integration Tests
- End-to-end workflow with real providers
- LLM integration tests
- Web search integration tests
- HITL workflow tests

### Staging Tests
- Test with real providers in staging environment
- Load testing with Postgres
- Failover testing

## Rollout Plan

### Phase 1: Staging (Week 1)
- Deploy to staging with mock providers
- Test with real providers (limited API keys)
- Monitor performance

### Phase 2: Production - Mock Providers (Week 2)
- Deploy to production with mock providers
- Monitor for issues
- Gather metrics

### Phase 3: Production - Real Providers (Week 3)
- Enable real providers for geocoding only
- Monitor and validate
- Enable remaining providers incrementally

### Phase 4: LLM Integration (Week 4)
- Enable LLM for one agent at a time
- Monitor LLM costs and performance
- Validate decision quality

## Risk Mitigation

### Provider API Failures
- Fallback to mock providers
- Retry logic with exponential backoff
- Circuit breaker pattern

### LLM Failures
- Fallback to deterministic logic
- Response validation
- Cost monitoring and limits

### Performance Issues
- Caching for provider responses
- Database connection pooling
- Request queuing

### Cost Control
- API call monitoring
- LLM cost tracking
- Rate limiting
- Budget alerts

## Success Metrics

### Provider Integration
- < 100ms average provider response time
- > 95% provider API success rate
- < $0.10 per quote provider cost

### LLM Integration
- < 500ms average LLM response time
- > 90% LLM decision accuracy
- < $0.50 per quote LLM cost

### HITL Workflow
- < 5 minute average HITL resolution time
- > 95% HITL task completion rate
- < 10% HITL escalation rate

### Production Scale
- Support 100+ concurrent requests
- < 1 second workflow latency
- > 99.9% uptime

## Dependencies

### New Python Packages
```
googlemaps>=4.10.0  # Google Maps API
requests>=2.31.0    # HTTP client
cachetools>=5.3.0   # Caching
tavily-python>=0.3.0  # Web search (or alternative)
psycopg2-binary>=2.9.9  # Postgres (if needed)
redis>=5.0.1        # Redis queue (if needed)
```

### External Services
- Google Maps API
- Property data provider API
- Hazard data provider API
- CLUE/insurance data API
- Web search API
- OpenAI API (for LLM)
- Postgres (if needed)
- Redis (if needed)

## Timeline

**Total Duration:** 6 weeks

**Sprint 1:** Provider Gateway & Real Integrations (Weeks 1-2)
**Sprint 2:** LLM Integration (Week 3)
**Sprint 3:** Web Search & HITL (Weeks 4-5)
**Sprint 4:** Production Scale (Week 6)

## Next Steps

1. Review and approve this plan
2. Set up development environment for Phase B
3. Begin Sprint 1: Provider Gateway & Real Integrations
4. Create feature branch for Phase B work
5. Set up staging environment for testing
