# Quick Start Guide - Agent B

Get up and running with Agent B in 5 minutes!

## 1. Prerequisites

- Python 3.9 or higher
- An Anthropic API key ([get one here](https://console.anthropic.com/))

## 2. Installation

```bash
# Clone or navigate to the project
cd agent-b-system

# Install dependencies
pip install -r requirements.txt

# Install Playwright browser
playwright install chromium
```

## 3. Configuration

Create a `.env` file:

```bash
cp .env.example .env
```

Edit `.env` and add your API key:

```
ANTHROPIC_API_KEY=sk-ant-api03-...your-key-here...
```

## 4. Run Your First Task

Create a file `my_first_task.py`:

```python
import asyncio
from src.main import DocumentationAgent

async def main():
    # Initialize the agent
    agent = DocumentationAgent(
        llm_provider="claude",
        model="claude-sonnet-4-20250514"
    )

    # Document a simple task
    result = await agent.document_task(
        question="How do I search for Python on Google?",
        app_url="https://www.google.com",
        output_dir="./my_first_guide"
    )

    # Check results
    print(f"✅ Success: {result['success']}")
    print(f"📸 Steps captured: {result['total_steps']}")
    print(f"📁 Guide saved to: {result['output_directory']}")
    print(f"🌐 Open HTML guide: {result['guides']['html']}")

if __name__ == "__main__":
    asyncio.run(main())
```

Run it:

```bash
python my_first_task.py
```

## 5. View Your Guide

The system will:
1. Open a browser (you'll see it!)
2. Navigate to Google
3. Perform the search task
4. Capture screenshots
5. Generate guides in 3 formats

Open the generated HTML guide:

```bash
open my_first_guide/guide.html
```

## 6. Try More Complex Tasks

```python
# Example: GitHub task
result = await agent.document_task(
    question="How do I navigate to the Python repository on GitHub?",
    app_url="https://github.com",
    output_dir="./github_guide"
)

# Example: Wikipedia search
result = await agent.document_task(
    question="How do I search for 'Machine Learning' on Wikipedia?",
    app_url="https://www.wikipedia.org",
    output_dir="./wikipedia_guide"
)
```

## 7. Customize Settings

Edit `config/settings.yaml`:

```yaml
browser:
  headless: false  # Set true to hide browser window

agent:
  max_steps: 50  # Maximum steps before timeout

screenshot:
  som_marker:
    background_color: "#FF0000"  # Change marker color
```

## Common Issues

### Issue: "API key not found"
**Solution**: Make sure `.env` file exists and contains valid `ANTHROPIC_API_KEY`

### Issue: "Browser fails to launch"
**Solution**: Run `playwright install chromium`

### Issue: "Module not found"
**Solution**: Make sure you're in the project directory and dependencies are installed

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Check [examples/basic_usage.py](examples/basic_usage.py) for more examples
- Run tests: `pytest tests/ -v`
- Configure for your use case in `config/settings.yaml`

## Architecture Overview

```
You ask a question
      ↓
Vision AI (Claude) analyzes the page
      ↓
Takes actions (click, type, navigate)
      ↓
Captures screenshots at key moments
      ↓
Generates beautiful guides
```

## Tips for Best Results

1. **Be specific in questions**: "How do I create a new project?" works better than "Tell me about projects"
2. **Start with simple sites**: Google, Wikipedia work great for testing
3. **Check the output**: Look at screenshots to understand what the agent saw
4. **Adjust max_steps**: Some tasks need more steps than others
5. **Use headless: false** for debugging - you can watch the agent work!

---

**Ready to document any web task automatically!** 🚀

For help: Check the [README.md](README.md) or open an issue on GitHub.
