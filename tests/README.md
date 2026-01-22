# Test Suite for gh-follower-changes

This directory contains the test suite for the `gh-follower-changes` project using pytest.

## Running Tests

### Run all tests
```bash
pytest tests/
```

### Run with verbose output
```bash
pytest tests/ -v
```

### Run with coverage report
```bash
pytest tests/ --cov=track_followers --cov-report=term-missing --cov-report=html
```

### Run specific test file
```bash
pytest tests/test_track_followers.py
```

### Run specific test class or function
```bash
pytest tests/test_track_followers.py::TestFollowerChanges
pytest tests/test_track_followers.py::TestFollowerChanges::test_empty_changes
```

## Test Structure

- `conftest.py` - Pytest configuration and shared fixtures
- `test_track_followers.py` - Unit tests for all functions and classes
- `test_integration.py` - Integration tests for the main function

## Test Coverage

The test suite provides comprehensive coverage including:

### Unit Tests
- **FollowerChanges dataclass** - Tests for the data model and its properties
- **validate_username** - Tests for username validation logic
- **load_followers/save_followers** - Tests for file I/O operations
- **compare_followers** - Tests for follower comparison logic
- **build_changelog_entry** - Tests for changelog entry generation
- **update_changelog** - Tests for changelog update logic including edge cases
- **fetch_followers** - Tests for API interaction with mocked responses
- **fatal** - Tests for error handling

### Integration Tests
- **main function** - End-to-end tests covering:
  - First run scenario (no previous data)
  - Detecting changes between runs
  - Handling no changes
  - Error handling
  - File naming and organization
  - Multi-day data accumulation

## Fixtures

The test suite uses the following pytest fixtures (defined in `conftest.py`):

- `temp_dir` - Temporary directory for test files
- `data_dir` - Temporary data directory for follower data
- `changelog_path` - Temporary changelog file path
- `sample_followers` - Sample follower data
- `sample_previous_followers` - Sample previous follower data

## Coverage Goals

The test suite aims for high code coverage (currently at 100%) to ensure:
- All functions are tested
- Edge cases are handled
- Error conditions are properly managed
- Integration between components works correctly
