# Contributing to Agent B

Thank you for your interest in contributing to Agent B! This document provides guidelines and instructions for contributing.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/yourusername/agent-b-system.git`
3. Create a branch: `git checkout -b feature/your-feature-name`
4. Make your changes
5. Run tests: `make test`
6. Commit: `git commit -m "Add your feature"`
7. Push: `git push origin feature/your-feature-name`
8. Create a Pull Request

## Development Setup

```bash
# Install dependencies
make install

# Set up environment
make setup
# Edit .env with your API keys

# Run tests
make test

# Run examples
make example
```

## Code Style

- Use Python 3.9+ features
- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Write docstrings for all public functions/classes
- Keep functions focused and concise

### Example

```python
async def execute_action(self, action: AgentAction) -> bool:
    """
    Execute an agent action.

    Args:
        action: AgentAction to execute

    Returns:
        bool: True if action succeeded, False otherwise
    """
    # Implementation
    pass
```

## Testing

- Write tests for new features
- Ensure existing tests pass
- Aim for >80% code coverage
- Use pytest for testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/test_browser.py -v

# Run with coverage
pytest tests/ --cov=src
```

## Areas for Contribution

### High Priority

1. **Login Flow Automation**
   - Generic login detection
   - Support for OAuth flows
   - 2FA handling

2. **Error Recovery**
   - Better error detection
   - Automatic retry logic
   - Self-healing when actions fail

3. **Additional LLM Providers**
   - Google Gemini support
   - Local LLM support (Ollama)
   - Custom model endpoints

### Medium Priority

4. **Enhanced State Detection**
   - Modal detection improvements
   - Animation completion detection
   - Loading spinner detection

5. **Multi-Tab Support**
   - Handle pop-ups
   - Track multiple tabs
   - Tab switching logic

6. **Video Recording**
   - Record full session as video
   - Generate video guides
   - Annotated playback

### Nice to Have

7. **Browser State Persistence**
   - Save/resume sessions
   - Cookie management
   - Session storage

8. **Interactive Mode**
   - Human-in-the-loop corrections
   - Manual intervention points
   - Training mode

9. **Performance Optimizations**
   - Parallel task execution
   - Caching mechanisms
   - Reduced API calls

## Pull Request Process

1. **Update Documentation**
   - Update README if adding features
   - Add docstrings to new functions
   - Update ARCHITECTURE.md if changing design

2. **Add Tests**
   - Unit tests for new components
   - Integration tests for workflows
   - Update test fixtures if needed

3. **Run Full Test Suite**
   ```bash
   make test
   ```

4. **Update CHANGELOG**
   - Add entry describing your changes
   - Follow existing format

5. **Submit PR**
   - Clear title and description
   - Reference any related issues
   - Request review from maintainers

## Code Review Guidelines

### For Contributors

- Be responsive to feedback
- Keep PRs focused and small
- Write clear commit messages
- Update based on review comments

### For Reviewers

- Be constructive and kind
- Focus on code quality and correctness
- Suggest improvements
- Approve when ready

## Component-Specific Guidelines

### Browser Automation (`src/browser/`)

- Always use async/await
- Handle timeouts gracefully
- Clean up resources (close pages, contexts)
- Log actions for debugging

### Vision Agent (`src/agent/`)

- Keep prompts concise and clear
- Handle API errors with retries
- Parse responses defensively
- Validate all outputs

### Detection (`src/detection/`)

- Tune thresholds carefully
- Document detection logic
- Provide configurable parameters
- Test with diverse websites

### Screenshot Management (`src/screenshot/`)

- Optimize image sizes
- Include rich metadata
- Support multiple formats
- Handle file I/O errors

## Reporting Issues

### Bug Reports

Include:
- Python version
- Operating system
- Steps to reproduce
- Expected vs actual behavior
- Error messages/logs
- Screenshots if applicable

### Feature Requests

Include:
- Use case description
- Expected behavior
- Why it's useful
- Possible implementation ideas

## Questions?

- Open a GitHub issue for questions
- Check existing issues first
- Be specific and provide context

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers
- Focus on constructive feedback
- Assume good intentions

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for contributing to Agent B!** 🚀
