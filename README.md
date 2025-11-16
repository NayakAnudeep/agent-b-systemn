# Agent B - AI Multi-Agent Web Task Documentation System

An intelligent system that automatically documents web-based tasks by navigating live web applications, capturing screenshots at meaningful UI states, and generating visual step-by-step guides.

## 🎯 Overview

**Agent B** receives questions like *"How do I create a project in Linear?"* from Agent A (or any user), automatically navigates the web app using vision-based AI, and returns a comprehensive visual guide showing exactly how to complete the task.

### Key Features

- 🤖 **Vision-Based Navigation**: Uses Claude 4.5 Sonnet (or GPT-4o) with computer vision to understand and navigate web UIs
- 🎨 **Set-of-Mark (SoM) Technology**: Overlays numbered markers on interactive elements for precise AI control
- 📸 **Intelligent Screenshot Capture**: Automatically detects meaningful UI states (modals, forms, confirmations)
- 🔍 **Multi-Modal State Detection**: Combines visual similarity, DOM changes, and network monitoring
- 📚 **Multiple Output Formats**: Generates Markdown, HTML, and JSON documentation guides
- 🌐 **Universal Web Support**: Works with any web application (SaaS tools, websites, web apps)
- 🔐 **Authentication Support**: Automatic login detection and execution for apps requiring authentication
- ⚡ **SPA Optimized**: Enhanced support for React, Vue, Angular and other Single Page Applications

## 🏗️ Architecture

```
┌─────────────┐
│  Agent A    │  ──── Question: "How do I create a project?"
│ (or User)   │
└──────┬──────┘
       │
       ▼
┌──────────────────────────────────────────────────────────┐
│                     Agent B System                        │
│                                                           │
│  ┌─────────────┐      ┌──────────────┐                  │
│  │   Vision    │◄────►│   Browser    │                  │
│  │    Agent    │      │  Controller  │                  │
│  │  (Claude)   │      │ (Playwright) │                  │
│  └─────────────┘      └──────────────┘                  │
│         │                     │                          │
│         ▼                     ▼                          │
│  ┌─────────────┐      ┌──────────────┐                  │
│  │   State     │      │ Screenshot   │                  │
│  │  Detector   │      │   Manager    │                  │
│  └─────────────┘      └──────────────┘                  │
│                              │                           │
│                              ▼                           │
│                       ┌──────────────┐                   │
│                       │    Guide     │                   │
│                       │  Generator   │                   │
│                       └──────────────┘                   │
└──────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────┐
│  Visual Step Guide   │
│  • Screenshots       │
│  • Descriptions      │
│  • Multiple formats  │
└──────────────────────┘
```

## 🚀 Quick Start

### Installation

1. **Clone the repository**
   ```bash
   cd agent-b-system
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Playwright browsers**
   ```bash
   playwright install chromium
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and add your API keys
   ```

   Required environment variables:
   - `ANTHROPIC_API_KEY` - Your Anthropic API key (for Claude)
   - `OPENAI_API_KEY` - Your OpenAI API key (optional, for GPT-4o)

### Basic Usage

```python
import asyncio
from src.main import DocumentationAgent

async def main():
    # Initialize agent
    agent = DocumentationAgent(
        llm_provider="claude",  # or "openai"
        model="claude-sonnet-4-20250514"
    )

    # Document a task
    result = await agent.document_task(
        question="How do I create a project in Linear?",
        app_url="https://linear.app",
        # Optional: provide credentials if login required
        credentials={"email": "user@example.com", "password": "..."}
    )

    # Results
    print(f"Success: {result['success']}")
    print(f"Screenshots: {result['total_steps']}")
    print(f"Duration: {result['total_duration']}")
    print(f"Guides: {result['guides']}")

asyncio.run(main())
```

### With Authentication (Linear, Notion, etc.)

For apps requiring login:

```python
import os
from dotenv import load_dotenv

load_dotenv()

result = await agent.document_task(
    question="How do I create a project in Linear?",
    app_url="https://linear.app",
    credentials={
        "email": os.getenv("LINEAR_EMAIL"),
        "password": os.getenv("LINEAR_PASSWORD")
    }
)
```

**Setup**: Add credentials to `.env` file:
```bash
LINEAR_EMAIL=your-email@example.com
LINEAR_PASSWORD=your-password
```

See [AUTHENTICATION.md](AUTHENTICATION.md) for detailed authentication guide.

### Run Examples

```bash
# Basic examples (no login required)
python examples/basic_usage.py

# Linear examples (requires credentials)
python examples/linear_example.py

# Notion examples (requires credentials)
python examples/notion_example.py
```

This will run example tasks and generate documentation guides in the `./output` directory.

## 📖 Documentation

### Core Components

#### 1. VisionWebAgent (`src/agent/vision_agent.py`)

The brain of the system. Uses vision LLM (Claude/GPT-4o) to:
- Analyze screenshots with SoM markers
- Understand current UI state
- Decide next actions
- Determine when to capture screenshots

```python
from src.agent.vision_agent import VisionWebAgent

agent = VisionWebAgent(
    provider="claude",
    model="claude-sonnet-4-20250514",
    api_key="your-api-key"
)

response = agent.decide_next_action(
    goal="Create a new project",
    current_state=page_state,
    screenshot_path="screenshot.png"
)
```

#### 2. BrowserController (`src/browser/controller.py`)

Manages browser automation with Playwright:
- Launches and controls browser
- Executes actions (click, type, navigate)
- Captures page state
- Integrates with SoM markers

```python
from src.browser.controller import BrowserController

controller = BrowserController()
await controller.start()
await controller.navigate("https://example.com")

state = await controller.get_current_state()
await controller.execute_action(action)

await controller.stop()
```

#### 3. SoMMarker (`src/browser/som_marker.py`)

Implements Set-of-Mark technique:
- Overlays numbered markers on interactive elements
- Returns element metadata
- Enables precise AI control

```python
from src.browser.som_marker import SoMMarker

marker = SoMMarker()
elements = await marker.mark_page(page)
# Returns: [{"marker_id": 0, "tag_name": "button", "text": "Create", ...}, ...]
```

#### 4. StateDetector (`src/detection/state_detector.py`)

Detects meaningful UI changes:
- Visual similarity comparison (SSIM)
- DOM hash tracking
- Decides when to capture screenshots

```python
from src.detection.state_detector import StateDetector

detector = StateDetector()
should_capture = detector.should_capture_screenshot(
    action_type="click",
    current_screenshot="current.png",
    current_dom_hash="abc123"
)
```

#### 5. ScreenshotManager (`src/screenshot/manager.py`)

Manages screenshot collection and metadata:
- Records screenshots with context
- Tracks step numbers
- Stores action metadata

#### 6. GuideGenerator (`src/screenshot/guide_generator.py`)

Generates documentation in multiple formats:
- **Markdown**: Simple text-based guide
- **HTML**: Rich, styled web page
- **JSON**: Structured data for integration

### Configuration

Edit `config/settings.yaml` to customize:

```yaml
llm:
  providers:
    claude:
      model: "claude-sonnet-4-20250514"
      max_tokens: 4096
      temperature: 0.7

browser:
  headless: false  # Set true for production
  viewport:
    width: 1280
    height: 720
  timeout: 30000

detection:
  visual_similarity_threshold: 0.95  # SSIM threshold
  dom_stability_checks: 3

screenshot:
  format: "png"
  som_marker:
    background_color: "#FF0000"
    text_color: "#FFFFFF"

agent:
  max_steps: 50  # Maximum steps to prevent infinite loops
```

## 🧪 Testing

Run the test suite:

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_browser.py -v
```

## 📊 Output Formats

### Markdown Guide

```markdown
# Task Guide: How do I create a project in Linear?

## Step 1: Navigate to Linear dashboard
**Action**: navigate
![Step 1](screenshot_001.png)

## Step 2: Click the '+' button
**Action**: click
**Target**: [12]
![Step 2](screenshot_002.png)
...
```

### HTML Guide

Professional, styled HTML page with embedded screenshots.

### JSON Guide

```json
{
  "task_goal": "How do I create a project in Linear?",
  "total_steps": 5,
  "steps": [
    {
      "step_number": 1,
      "description": "Navigate to Linear dashboard",
      "action_type": "navigate",
      "screenshot_path": "./output/screenshot_001.png",
      "timestamp": 1234567890.123
    },
    ...
  ]
}
```

## 🔬 Technical Approach

### Set-of-Mark (SoM) Prompting

Based on Microsoft Research's technique, we overlay numbered markers on interactive elements:

```javascript
// Example of SoM implementation
[0] Button: "Create Project"
[1] Link: "Settings"
[2] Input: "Search..."
```

The LLM can then reference elements precisely: `"Click element [0] to create a project"`

### Multi-Modal Perception

Combines multiple inputs for robust understanding:
1. **Visual**: Screenshot with SoM markers
2. **Structural**: Accessibility tree of elements
3. **Contextual**: URL, page title, action history

### Intelligent Screenshot Capture

Captures screenshots when:
- ✅ Modal/dialog opens
- ✅ Form submission completes
- ✅ Major UI state changes (new page, panel opens)
- ✅ Task milestones reached

Skips screenshots for:
- ❌ Hover states
- ❌ Minor UI changes (tooltips, dropdowns)
- ❌ Every single action

## 🎓 Research References

This system implements cutting-edge research from 2024-2025:

1. **Set-of-Mark (SoM)** - Microsoft Research
   - Used in Magma multimodal model
   - Enables precise element reference

2. **BrowserGym** - ServiceNow Research
   - Standardized environment for web agents
   - Benchmark support (WorkArena, WebArena)

3. **Claude 3.5 Sonnet Computer Use** - Anthropic
   - State-of-the-art web task performance (39.1% on WorkArena L2)
   - Native computer use capabilities

4. **Visual Grounding** - VisualWebArena (ICLR 2024)
   - Multi-modal perception improves accuracy 2-3x

## 🛠️ Advanced Usage

### Custom Configuration

```python
agent = DocumentationAgent(
    llm_provider="claude",
    model="claude-sonnet-4-20250514",
    config_path="./custom_config.yaml"
)
```

### Handling Authentication

```python
result = await agent.document_task(
    question="How do I create a project?",
    app_url="https://app.example.com",
    credentials={
        "email": "user@example.com",
        "password": "secure_password"
    }
)
```

### Integration with Agent A

```python
# Agent A calls Agent B
from src.main import DocumentationAgent

class AgentA:
    def __init__(self):
        self.doc_agent = DocumentationAgent(llm_provider="claude")

    async def get_task_guide(self, user_question):
        # Extract task and URL from question
        task = "How do I create a project in Linear?"
        url = "https://linear.app"

        # Get documentation
        guide = await self.doc_agent.document_task(
            question=task,
            app_url=url
        )

        return guide
```

## 📝 Project Structure

```
agent-b-system/
├── src/
│   ├── agent/
│   │   ├── vision_agent.py      # Vision LLM controller
│   │   ├── prompts.py            # Prompt templates
│   │   └── schemas.py            # Data schemas
│   ├── browser/
│   │   ├── controller.py         # Browser automation
│   │   ├── som_marker.py         # Set-of-Mark implementation
│   │   └── action_executor.py    # Action execution
│   ├── detection/
│   │   └── state_detector.py     # UI change detection
│   ├── screenshot/
│   │   ├── manager.py            # Screenshot management
│   │   └── guide_generator.py    # Output generation
│   └── main.py                    # Main orchestrator
├── tests/                         # Test suite
├── examples/                      # Usage examples
├── config/
│   └── settings.yaml             # Configuration
├── requirements.txt              # Dependencies
├── .env.example                  # Environment template
└── README.md                     # This file
```

## 🐛 Troubleshooting

### Browser doesn't launch
```bash
# Reinstall Playwright browsers
playwright install chromium --force
```

### API key errors
```bash
# Check your .env file
cat .env

# Verify API key is set
echo $ANTHROPIC_API_KEY
```

### Element detection issues
- Increase `visual_similarity_threshold` in config
- Set `headless: false` to debug visually
- Check logs for element detection output

## 🤝 Contributing

Contributions welcome! Areas for improvement:

- [ ] Login flow automation
- [ ] Additional LLM providers (Gemini, etc.)
- [ ] Enhanced error recovery
- [ ] Browser state persistence
- [ ] Multi-tab support
- [ ] Video recording option

## 📄 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

- **Anthropic** - Claude 4.5 Sonnet vision capabilities
- **Microsoft Research** - Set-of-Mark technique
- **ServiceNow** - BrowserGym framework
- **Playwright** - Browser automation

---

**Built with ❤️ for Agent A and the future of automated documentation**

For questions or issues, please open a GitHub issue.
