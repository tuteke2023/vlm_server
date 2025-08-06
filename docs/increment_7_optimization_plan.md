# Increment 7: Performance Optimization and Cleanup Plan

## Performance Analysis Results

### Current Performance Metrics
- **LangChain Endpoint**: 76.52s (17 transactions extracted)
- **JSON Endpoint**: 32.74s (10 transactions extracted)
- **Performance Gap**: LangChain is 133.7% slower
- **VRAM Usage**: 58.4% (9.31 GB allocated, 6.28 GB free)

### Key Findings
1. LangChain provides better extraction quality (17 vs 10 transactions)
2. The performance overhead comes from:
   - Multiple parsing attempts (direct parse → manual JSON → fixing parser)
   - Sync/async conversion overhead in LangChain wrapper
   - Complex prompt template processing

## Optimization Strategy

### 1. Performance Optimizations

#### A. Optimize LangChain Extraction (Priority: High)
- **Problem**: Multiple parsing attempts add latency
- **Solution**: 
  - Skip direct Pydantic parsing for VLM (go straight to manual JSON parse)
  - Cache compiled regex patterns
  - Optimize JSON cleaning operations

#### B. Add Response Caching (Priority: Medium)
- **Problem**: Repeated identical requests hit the model
- **Solution**:
  - Implement LRU cache for recent extractions
  - Cache key: hash of image + prompt
  - TTL: 15 minutes

#### C. Optimize Unified Provider (Priority: Low)
- **Problem**: Minor overhead from abstraction layer
- **Solution**:
  - Remove unnecessary async conversions
  - Streamline message formatting

### 2. Code Cleanup

#### A. Remove Legacy Code
- `bank_parser.py` (superseded by v3)
- `bank_parser_v2.py` (superseded by v3)
- Old test files for deprecated parsers
- Duplicate endpoint implementations

#### B. Consolidate Endpoints
- Merge duplicate provider switching endpoints
- Remove legacy generate endpoint (keep unified)
- Consolidate health check logic

#### C. Frontend Cleanup
- Remove old `index.html` (use `index_unified_styled.html`)
- Remove duplicate JavaScript files
- Clean up unused CSS

### 3. Memory Optimizations

#### A. Garbage Collection
- Force GC after large extractions
- Clear image buffers after processing

#### B. Model Loading
- Lazy load processors only when needed
- Optimize batch size for inference

### 4. Documentation Updates

#### A. API Documentation
- Document unified endpoints
- Deprecation notices for legacy endpoints
- Performance tuning guide

#### B. Deployment Guide
- Production configuration
- Environment variables
- Monitoring setup

## Implementation Order

1. **Quick Wins** (< 1 hour)
   - Optimize JSON parsing in LangChain extractor
   - Cache regex patterns
   - Remove obvious duplicate files

2. **Medium Tasks** (1-2 hours)
   - Implement response caching
   - Consolidate endpoints
   - Update documentation

3. **Larger Tasks** (2-4 hours)
   - Full frontend consolidation
   - Comprehensive testing
   - Deployment guide

## Expected Results

- LangChain performance improvement: 30-40% faster
- Reduced codebase size: ~30% fewer files
- Better maintainability
- Production-ready system