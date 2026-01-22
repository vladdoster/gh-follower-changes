This is a Python based repository. It is primarily responsible for ingesting a GitHub user followers and recording changes. Please follow these guidelines when contributing:

## Code Standards

### Required Before Each Commit
- Run `uvx black -l 120 *.py` & `uvx isort --force-sort-within-sections -m BACKSLASH_GRID -l 120 --force-alphabetical-sort-within-sections *.py`  before committing any changes to ensure proper code formatting
- This will run isort and black on all Python files to maintain consistent style

### Development Flow
- Build: `uv sync`
- Test: `uv run --group dev pytest --cov-branch --cov=track_followers tests/`

## Repository Structure
- `pyproject.toml`: Program details and uses semantic versioning: `pyproject.toml`
- `tests/`: Test helpers and fixtures
- `track_followers.py`: Program entry points containing logic related to interactions with GitHub API and updating `CHANGELOG.md`

## Key Guidelines
1. Follow Python best practices and idiomatic patterns
2. Maintain existing code structure and organization
3. Use OOP, DRY, and dependency injection patterns where appropriate
4. Write unit tests for new functionality. Use mock unit tests when possible.
5. Document complex logic. Suggest changes to the `docs/` folder when appropriate
