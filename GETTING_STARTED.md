# Getting Started with Agent B

A step-by-step guide to get Agent B running in minutes.

## 📋 Prerequisites

Before you begin, ensure you have:

- ✅ **Python 3.9+** installed
  ```bash
  python3 --version  # Should show 3.9 or higher
  ```

- ✅ **pip** package manager
  ```bash
  pip --version
  ```

- ✅ **Anthropic API Key** ([Sign up here](https://console.anthropic.com/))

## 🚀 Installation (5 minutes)

### Step 1: Navigate to Project Directory

```bash
cd agent-b-system
```

### Step 2: Install Python Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- Playwright (browser automation)
- Anthropic SDK (Claude AI)
- Computer vision libraries (OpenCV, scikit-image)
- Utilities (PyYAML, Pydantic, loguru)

**Expected time**: 2-3 minutes

### Step 3: Install Playwright Browser

```bash
playwright install chromium
```

This downloads the Chromium browser that Agent B will control.

**Expected time**: 1-2 minutes

### Step 4: Set Up Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit the file and add your API key
nano .env  # or use your favorite editor
```

In `.env`, add:
```
ANTHROPIC_API_KEY=sk-ant-api03-YOUR-KEY-HERE
```

Save and exit.

## ✅ Verify Installation

Run this quick check:

```bash
python3 -c "import playwright; import anthropic; import yaml; print('✅ All dependencies installed!')"
```

If you see the success message, you're ready!

## 🎯 Your First Task (2 minutes)

Let's document a simple web task: searching on Google.

### Create a Test Script

Create `test_agent.py`:

```python
import asyncio
from src.main import DocumentationAgent

async def main():
    print("🤖 Starting Agent B...")

    # Initialize the agent
    agent = DocumentationAgent(
        llm_provider="claude",
        model="claude-sonnet-4-20250514"
    )

    # Document the task
    print("\n📝 Documenting task: Google search")
    result = await agent.document_task(
        question="How do I search for 'Python programming' on Google?",
        app_url="https://www.google.com",
        output_dir="./my_first_guide",
        max_steps=10  # Limit steps for quick test
    )

    # Show results
    print("\n" + "="*60)
    print("✅ TASK COMPLETE!")
    print("="*60)
    print(f"Success: {result['success']}")
    print(f"Screenshots: {result.get('total_steps', 0)}")
    print(f"Duration: {result.get('total_duration', 'N/A')}")
    print(f"\n📁 Output directory: {result.get('output_directory', 'N/A')}")

    if result.get('guides'):
        print("\n📚 Generated guides:")
        for format_type, path in result['guides'].items():
            print(f"  • {format_type.upper()}: {path}")

    print("\n💡 Open the HTML guide to see the results!")
    print(f"   open {result['guides']['html']}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Run Your First Task

```bash
python3 test_agent.py
```

### What You'll See

1. **Browser Opens**: A Chromium window will appear
2. **Agent Works**: You'll see it navigate to Google
3. **Actions Execute**: Search box fills, search executes
4. **Screenshots Captured**: Key moments are saved
5. **Guides Generated**: 3 formats created

**Expected time**: 30-60 seconds

### View the Results

```bash
# Open the HTML guide
open my_first_guide/guide.html

# Or check all generated files
ls -la my_first_guide/
```

You should see:
- `guide.md` - Markdown guide
- `guide.html` - Styled HTML guide
- `guide.json` - JSON data
- `state_*.png` - Screenshot files

## 🎨 What Just Happened?

Agent B:

1. ✅ Launched a browser
2. ✅ Navigated to Google
3. ✅ Used Claude's vision AI to understand the page
4. ✅ Identified the search box using Set-of-Mark markers
5. ✅ Typed "Python programming"
6. ✅ Clicked the search button
7. ✅ Captured screenshots at key moments
8. ✅ Generated documentation in 3 formats

All automatically!

## 🔧 Common Issues & Solutions

### Issue 1: "ANTHROPIC_API_KEY not found"

**Solution**:
```bash
# Check if .env exists
ls -la .env

# Verify the key is set
cat .env | grep ANTHROPIC_API_KEY

# Make sure there are no extra spaces
ANTHROPIC_API_KEY=sk-ant-...  # Good
ANTHROPIC_API_KEY = sk-ant-... # Bad (spaces)
```

### Issue 2: "playwright not found"

**Solution**:
```bash
# Reinstall Playwright
pip install playwright --force-reinstall
playwright install chromium
```

### Issue 3: "Browser fails to launch"

**Solution**:
```bash
# Try installing with sudo (macOS/Linux)
sudo playwright install chromium

# Or install all browsers
playwright install
```

### Issue 4: "Module 'src' not found"

**Solution**:
```bash
# Make sure you're in the project directory
pwd  # Should show .../agent-b-system

# Check if src/ exists
ls -la src/

# Run from project root, not from subdirectory
```

### Issue 5: "API rate limit exceeded"

**Solution**:
- Wait a few minutes before retrying
- Check your Anthropic dashboard for rate limits
- Consider upgrading your API tier

## 🎓 Next Steps

### Try Different Tasks

**Wikipedia Search**:
```python
result = await agent.document_task(
    question="How do I search for 'Artificial Intelligence' on Wikipedia?",
    app_url="https://www.wikipedia.org",
    output_dir="./wikipedia_guide"
)
```

**GitHub Navigation**:
```python
result = await agent.document_task(
    question="How do I navigate to the Python repository on GitHub?",
    app_url="https://github.com",
    output_dir="./github_guide"
)
```

### Customize Configuration

Edit `config/settings.yaml`:

```yaml
browser:
  headless: false  # Set true to hide browser window

agent:
  max_steps: 50  # Increase for complex tasks

screenshot:
  som_marker:
    background_color: "#00FF00"  # Green markers instead of red
```

### Run the Examples

```bash
python examples/basic_usage.py
```

This runs multiple example tasks sequentially.

### Read the Documentation

- **Quick Reference**: [QUICKSTART.md](QUICKSTART.md)
- **Full Documentation**: [README.md](README.md)
- **Architecture**: [ARCHITECTURE.md](ARCHITECTURE.md)
- **Contributing**: [CONTRIBUTING.md](CONTRIBUTING.md)

## 💡 Pro Tips

1. **Watch the Browser**
   - Set `headless: false` to see what Agent B sees
   - Great for debugging and understanding

2. **Start Simple**
   - Test with simple sites first (Google, Wikipedia)
   - Move to complex apps once confident

3. **Check Logs**
   - Agent B logs everything
   - Look for ERROR or WARNING messages

4. **Adjust max_steps**
   - Simple tasks: 5-10 steps
   - Medium tasks: 20-30 steps
   - Complex tasks: 40-50 steps

5. **Review Screenshots**
   - Check what the agent captured
   - Helps understand if detection is working

## 🧪 Testing Your Installation

Run the test suite:

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest tests/ -v
```

All tests should pass!

## 📊 Understanding Output

### Directory Structure

```
my_first_guide/
├── guide.md           # Markdown guide
├── guide.html         # HTML guide (open this!)
├── guide.json         # JSON data
├── state_*.png        # Screenshots with markers
```

### HTML Guide Features

- 📸 Embedded screenshots
- 🎨 Professional styling
- 📝 Step-by-step descriptions
- 🏷️ Action badges
- 📱 Responsive design

### JSON Data Structure

```json
{
  "task_goal": "How do I...",
  "total_steps": 5,
  "steps": [
    {
      "step_number": 1,
      "description": "...",
      "action_type": "click",
      "screenshot_path": "...",
      "timestamp": 1234567890
    }
  ]
}
```

## 🤝 Getting Help

### Resources

1. **Documentation**: Check the docs/ folder
2. **Examples**: See examples/basic_usage.py
3. **Issues**: Open a GitHub issue
4. **Community**: Join discussions

### Before Asking for Help

Include:
- ✅ Python version (`python3 --version`)
- ✅ Operating system
- ✅ Error message (full output)
- ✅ Steps to reproduce
- ✅ What you expected vs what happened

## 🎉 Success!

You've successfully:
- ✅ Installed Agent B
- ✅ Configured API keys
- ✅ Run your first task
- ✅ Generated documentation guides

You're ready to document any web task automatically!

## 🚀 What's Next?

Choose your path:

**Path 1: Explore**
- Try different websites
- Experiment with complex tasks
- Customize the configuration

**Path 2: Integrate**
- Use Agent B in your projects
- Build Agent A integration
- Create custom workflows

**Path 3: Contribute**
- Add new features
- Improve documentation
- Share your use cases

---

**Need help?** Check [QUICKSTART.md](QUICKSTART.md) or [README.md](README.md)

**Ready to go deeper?** Read [ARCHITECTURE.md](ARCHITECTURE.md)

**Happy documenting!** 🎊
