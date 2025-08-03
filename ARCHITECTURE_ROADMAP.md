# Architecture Roadmap - AI Platform

## Document Purpose
This document captures the architectural decisions made on 2025-08-03 and outlines the evolution path from a monolithic application to a scalable microservices platform.

## Current State (August 2025)
- Single VLM server with bank statement processing
- Working with RTX 5060 Ti after resolving CUDA compatibility issues
- Need to add audio transcription without breaking existing functionality

## Problem Statement
Yesterday (2025-08-02), we attempted to add audio transcription features directly to the VLM server, which led to:
- Dependency conflicts
- Lost virtual environment context during multiple restarts
- CUDA compatibility issues (though this was actually due to wrong Python environment)
- System instability requiring rollback to commit 59e9878

## Architectural Decision
**Decision**: Adopt a progressive microservices approach starting with a monorepo structure.

**Rationale**:
1. Prevents dependency conflicts between services
2. Allows independent scaling and deployment
3. Enables technology diversity (different Python versions, frameworks)
4. Provides clear failure isolation
5. Supports future growth without major refactoring

## Implementation Phases

### Phase 1: Monorepo with Service Separation (Current - Q3 2025)
```
vlm_server/
├── services/
│   ├── vlm/                    # Existing VLM functionality
│   │   ├── vlm_server.py
│   │   ├── requirements.txt
│   │   ├── Dockerfile
│   │   └── web_interface/
│   └── audio/                  # New audio transcription
│       ├── transcription_server.py
│       ├── requirements.txt
│       ├── Dockerfile
│       └── web_interface/
├── scripts/
│   ├── start_all.sh           # Start all services
│   ├── start_vlm.sh           # Start VLM only
│   └── start_audio.sh         # Start audio only
├── docker-compose.yml         # Local development
├── README.md
└── ARCHITECTURE_ROADMAP.md    # This document
```

**Benefits**:
- Simple to manage while learning microservices patterns
- Each service has isolated dependencies
- Can run services independently or together
- Easy to add new services

### Phase 2: API Gateway & Service Discovery (Q4 2025 - When 3+ services)
```
ai-platform/
├── gateway/                   # NGINX or Kong API Gateway
│   ├── nginx.conf
│   └── routes/
├── services/
│   ├── vlm/
│   ├── audio/
│   ├── document-qa/          # New service example
│   └── translation/          # New service example
├── web-frontend/             # Unified React/Vue frontend
└── docker-compose.yml        # Orchestration
```

**Trigger**: When we have 3+ services or need unified authentication

### Phase 3: Separate Repositories (2026 - When team grows)
```
Organization: ai-platform/
├── vlm-service/              # GitHub repo
├── audio-service/            # GitHub repo
├── document-qa-service/      # GitHub repo
├── api-gateway/              # GitHub repo
├── web-frontend/             # GitHub repo
└── platform-docs/            # GitHub repo
```

**Trigger**: 
- Multiple developers working on different services
- Need for independent versioning
- Different deployment schedules

### Phase 4: Cloud Native (Future - Based on scale)
- Kubernetes deployment
- Service mesh (Istio/Linkerd)
- Cloud provider managed services (AWS/GCP/Azure)
- Auto-scaling based on load

## Technical Standards

### 1. Service Communication
- **Internal**: REST APIs over HTTP (simple to start)
- **Future**: gRPC for inter-service communication
- **Format**: JSON (consider Protocol Buffers later)

### 2. Service Ports
- VLM Service: 8000
- Audio Service: 8001
- Document QA: 8002
- Translation: 8003
- API Gateway: 80/443
- Web Frontend: 8080

### 3. Environment Management
- Each service has its own virtual environment
- Docker containers for production consistency
- Environment variables for configuration

### 4. GPU Resource Management
```yaml
# docker-compose.yml example
services:
  vlm:
    environment:
      - CUDA_VISIBLE_DEVICES=0
      - MAX_MEMORY_GB=8
  audio:
    environment:
      - CUDA_VISIBLE_DEVICES=0
      - MAX_MEMORY_GB=4
```

### 5. Naming Conventions
- Service names: `<function>-service` (vlm-service, audio-service)
- Endpoints: `/api/v1/<resource>`
- Environment variables: `<SERVICE>_<VARIABLE>` (VLM_PORT, AUDIO_MODEL)

## Migration Strategy

### From Current to Phase 1
1. Create `services/vlm/` directory
2. Move existing files maintaining functionality
3. Create `services/audio/` for new transcription service
4. Add docker-compose.yml for local development
5. Update documentation

### Service Template
Each new service should have:
```
service-name/
├── src/
│   └── main.py              # Main application
├── tests/
│   └── test_main.py         # Unit tests
├── requirements.txt         # Python dependencies
├── Dockerfile              # Container definition
├── README.md               # Service documentation
└── .env.example            # Environment variables
```

## Risk Mitigation

1. **Dependency Conflicts**: Isolated environments per service
2. **GPU Memory**: Implement memory limits and monitoring
3. **Service Communication**: Health checks and circuit breakers
4. **Data Consistency**: Event sourcing for critical operations
5. **Debugging**: Centralized logging (ELK stack later)

## Success Metrics

- [ ] Services can be developed independently
- [ ] Services can be deployed independently
- [ ] Single service failure doesn't affect others
- [ ] New services can be added in < 1 day
- [ ] Clear ownership boundaries

## Lessons Learned

1. **Virtual Environment Discipline**: Always activate the correct environment
2. **Dependency Isolation**: Don't mix unrelated functionalities
3. **Incremental Changes**: Big bang migrations often fail
4. **Documentation**: Capture decisions when made, not later
5. **GPU Compatibility**: Test with exact hardware early

## Next Steps

1. Create service directory structure
2. Move VLM code to `services/vlm/`
3. Implement audio transcription in `services/audio/`
4. Create docker-compose.yml
5. Update CI/CD pipelines

---

*Document created: 2025-08-03*  
*Last updated: 2025-08-03*  
*Author: System Architecture Team*