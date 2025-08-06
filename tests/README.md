# VLM Server Test Suite

This directory contains comprehensive tests for the unified LangChain implementation of the VLM server.

## Test Structure

```
tests/
├── unit/                    # Unit tests for individual components
│   ├── test_unified_llm_provider.py
│   └── test_langchain_extractor.py
├── integration/             # Integration tests
│   └── test_bank_extraction_integration.py
├── e2e/                    # End-to-end UI tests
│   └── test_web_ui_e2e.py
├── performance/            # Performance and validation tests
│   ├── test_performance.py
│   └── test_validation.py
├── data/                   # Test data files
│   ├── sample_bank_statement.txt
│   └── edge_cases.json
├── expected_outputs/       # Expected test outputs
│   ├── sample_bank_statement_expected.json
│   └── sample_bank_statement_expected.csv
├── MANUAL_TESTING_CHECKLIST.md  # Manual testing guide
├── pytest.ini              # pytest configuration
├── requirements-test.txt   # Test dependencies
└── README.md              # This file
```

## Quick Start

### 1. Install Test Dependencies

```bash
# Activate virtual environment
source ~/pytorch-env/bin/activate

# Install test dependencies
pip install -r tests/requirements-test.txt
```

### 2. Run All Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=services/vlm --cov-report=html

# Run specific test category
pytest tests/ -m unit
pytest tests/ -m integration
pytest tests/ -m e2e
pytest tests/ -m performance
```

### 3. Run Specific Test Files

```bash
# Unit tests
pytest tests/unit/test_unified_llm_provider.py -v
pytest tests/unit/test_langchain_extractor.py -v

# Integration tests
pytest tests/integration/test_bank_extraction_integration.py -v

# E2E tests (requires Selenium)
pytest tests/e2e/test_web_ui_e2e.py -v

# Performance tests
pytest tests/performance/test_performance.py -v
pytest tests/performance/test_validation.py -v
```

## Test Categories

### Unit Tests
Test individual components in isolation:
- UnifiedLLMProvider functionality
- LangChainExtractor operations
- Provider switching logic
- Message format conversion
- Error handling

### Integration Tests
Test component interactions:
- Complete bank extraction pipeline
- Provider fallback mechanisms
- API endpoint integration
- CSV/JSON export functionality

### E2E Tests
Test complete user workflows:
- Web UI interactions
- Provider selection
- File uploads
- Privacy warnings
- Export functionality

### Performance Tests
Test system performance:
- Response time benchmarks
- Concurrent request handling
- Memory usage monitoring
- Token efficiency
- Cache performance

### Validation Tests
Test extraction accuracy:
- Transaction count accuracy
- Amount extraction precision
- Date format consistency
- Category assignment
- Balance calculations

## Environment Setup

### Required Environment Variables

Create a `.env` file in the project root:

```bash
OPENAI_API_KEY=your_api_key_here
ALLOW_EXTERNAL_API_FOR_SENSITIVE_DOCS=false
DEFAULT_LLM_PROVIDER=local
```

### Test Data

Test bank statements are located in:
- `tests/BankStatementChequing.png` - Main test image
- `tests/data/` - Additional test cases

## Running Manual Tests

Follow the comprehensive checklist in `MANUAL_TESTING_CHECKLIST.md` for manual testing procedures.

## Continuous Integration

### GitHub Actions Workflow

```yaml
# Example CI configuration
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r tests/requirements-test.txt
      - name: Run tests
        run: pytest tests/ --cov=services/vlm
```

## Writing New Tests

### Test Naming Convention

- Test files: `test_<component_name>.py`
- Test classes: `Test<ComponentName>`
- Test methods: `test_<specific_functionality>`

### Example Test Structure

```python
import pytest
from unittest.mock import Mock, patch

class TestNewComponent:
    @pytest.fixture
    def component(self):
        """Create component instance"""
        return NewComponent()
    
    def test_basic_functionality(self, component):
        """Test basic component operation"""
        result = component.process("input")
        assert result == "expected_output"
    
    @pytest.mark.asyncio
    async def test_async_operation(self, component):
        """Test async functionality"""
        result = await component.async_process("input")
        assert result is not None
```

## Debugging Tests

### Run tests with debugging output:

```bash
# Verbose output
pytest tests/ -v

# Show print statements
pytest tests/ -s

# Stop on first failure
pytest tests/ -x

# Enter debugger on failure
pytest tests/ --pdb
```

### View test coverage report:

```bash
# Generate HTML coverage report
pytest tests/ --cov=services/vlm --cov-report=html

# Open coverage report
open htmlcov/index.html
```

## Performance Benchmarking

After running performance tests, check:
- `tests/performance/performance_report.json` - Detailed metrics
- `tests/performance/performance_metrics.png` - Visual charts

## Known Issues

1. **Selenium Tests**: E2E tests require Chrome/Chromium and ChromeDriver
2. **GPU Tests**: Some tests require CUDA-capable GPU
3. **API Tests**: OpenAI tests require valid API key

## Contributing

When adding new features:
1. Write unit tests first (TDD approach)
2. Add integration tests for component interactions
3. Update E2E tests if UI changes
4. Run full test suite before committing
5. Update this README if test structure changes

## Support

For test-related issues:
- Check test logs in `pytest` output
- Review coverage reports for untested code
- Consult MANUAL_TESTING_CHECKLIST.md for manual verification
- Create GitHub issues for test failures