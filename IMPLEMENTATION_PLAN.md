# Incremental Implementation Plan for Unified LangChain Integration

## Overview
We'll implement the solution in small, testable increments. Each increment will be fully tested before moving to the next.

## Implementation Increments

### Increment 1: Base UnifiedLLMProvider with Local VLM
**Goal:** Create provider abstraction with local VLM support only

**Tasks:**
1. Create `unified_llm_provider.py` with base structure
2. Implement local VLM provider wrapper
3. Add basic message handling
4. Test with existing endpoints

**Success Criteria:**
- Existing functionality works unchanged
- Can call local VLM through unified interface
- All current tests pass

---

### Increment 2: Add OpenAI Provider to Unified System
**Goal:** Integrate OpenAI provider into unified system

**Tasks:**
1. Update `unified_llm_provider.py` to support multiple providers
2. Integrate existing `openai_provider.py`
3. Implement provider switching logic
4. Add sensitive content detection

**Success Criteria:**
- Can switch between local and OpenAI
- Privacy warnings work correctly
- Fallback mechanism functions

---

### Increment 3: Create LangChain LLM Wrapper
**Goal:** Create custom LangChain LLM that uses UnifiedLLMProvider

**Tasks:**
1. Create `langchain_llm.py` with custom LLM class
2. Implement _call and _acall methods
3. Add proper error handling
4. Test with simple LangChain chains

**Success Criteria:**
- LangChain can use our unified provider
- Works with both local and OpenAI
- Async operations supported

---

### Increment 4: Create LangChainExtractor
**Goal:** Build extraction logic using LangChain

**Tasks:**
1. Create `langchain_extractor.py`
2. Implement bank extraction chain
3. Add structured output parsing
4. Integrate with existing parser

**Success Criteria:**
- Can extract bank statements using LangChain
- Structured output matches current format
- Fallback parsing still works

---

### Increment 5: Update VLM Server Endpoints
**Goal:** Update server to use new unified system

**Tasks:**
1. Update `vlm_server.py` to use UnifiedLLMProvider
2. Modify bank extraction endpoints
3. Ensure backward compatibility
4. Update metadata handling

**Success Criteria:**
- All endpoints work with new system
- Provider switching via API works
- Response formats unchanged

---

### Increment 6: Consolidate Frontend Code
**Goal:** Update UI to use unified approach

**Tasks:**
1. Update shared extraction logic
2. Consolidate duplicate code
3. Test both UI pages
4. Ensure consistent behavior

**Success Criteria:**
- Both pages use same extraction logic
- Provider switching works on all pages
- Export functionality consistent

---

### Increment 7: Performance Optimization
**Goal:** Optimize and clean up

**Tasks:**
1. Add caching where appropriate
2. Optimize token usage
3. Clean up old code
4. Update documentation

**Success Criteria:**
- Performance meets or exceeds current
- Code is clean and maintainable
- All tests pass

---

## Testing Strategy for Each Increment

### After Each Increment:
1. **Unit Tests**: Run relevant unit tests
2. **Integration Tests**: Test component interactions
3. **Manual Testing**: Follow relevant checklist items
4. **Regression Testing**: Ensure existing features work

### Quick Test Commands:
```bash
# Quick unit tests for current increment
python tests/run_tests.py --type unit --verbose

# Integration test
python tests/run_tests.py --type integration

# Manual smoke test
- Start server
- Test basic extraction
- Check both providers
```

## Rollback Strategy

Each increment will be committed separately:
```bash
git add .
git commit -m "Increment X: [description]"
```

If issues arise, we can easily rollback:
```bash
git revert HEAD
```

## Let's Start!

Ready to begin with Increment 1? We'll create the base UnifiedLLMProvider with local VLM support only.