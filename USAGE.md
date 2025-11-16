# Agent B - Web Automation Assistant

Agent B is a vision-based web automation agent that can control any web application using natural language commands.

## Quick Start

```bash
python chat_agent_general.py
```

## How It Works

1. **Select Application**: When you start, Agent B asks which app you want to use
2. **Auto-Login**: If credentials are in `.env`, it automatically logs in
3. **Execute Tasks**: Give natural language commands to automate tasks

## Example Session

```
🤖 AGENT B - WEB AUTOMATION ASSISTANT
======================================================================

📋 Supported applications:
  • asana
  • clickup
  • github
  • jira
  • linear
  • notion
  • slack
  • trello

🔹 Which application do you want to use? (or 'skip' for manual navigation): linear

✅ Found credentials for linear (your@email.com)
💡 I'll open the browser and navigate to linear when you give me your first command.

💬 You: create a new project called Bug Tracker

⏳ Starting browser for the first time...
✅ Browser started
⏳ Navigating to linear (https://linear.app)...
✅ Navigated to linear
⏳ Logging in as your@email.com...
✅ Successfully logged in to linear!
----------------------------------------------------------------------

🔄 Executing: create a new project called Bug Tracker

📍 Step 1/20
  Action: click
  Reasoning: Need to open the project creation modal
  Description: Click the 'New Project' button

📍 Step 2/20
  Action: type
  Reasoning: Entering the project name
  Description: Type 'Bug Tracker' in the name field

... (more steps)

✅ Task completed successfully!
🤖 Agent B: ✅ Created new project 'Bug Tracker'
   Completed in 5 steps
```

## Setting Up Credentials

Add credentials to `.env` file using this pattern:

```bash
# Pattern: {APP_NAME}_EMAIL and {APP_NAME}_PASSWORD

# Notion
NOTION_EMAIL=your@email.com
NOTION_PASSWORD=yourpassword

# Linear
LINEAR_EMAIL=your@email.com
LINEAR_PASSWORD=yourpassword

# GitHub
GITHUB_EMAIL=your@email.com
GITHUB_PASSWORD=yourpassword
```

**Supported Apps:**
- Notion
- Linear
- GitHub
- Jira
- Asana
- Trello
- Slack
- ClickUp

## Commands

### Navigation
- `go to [URL]` - Navigate to any website
- `navigate to [URL]` - Same as above
- `open [URL]` - Same as above

### System
- `help` - Show help message
- `status` - Show current browser status and URL
- `exit` - Close browser and quit

### Task Examples
- `Create a new page called 'Meeting Notes'`
- `Click the sign up button`
- `Fill in the email field with test@example.com`
- `Create a database for tracking projects`
- `Add a new task to the list`
- `Create a new issue in GitHub`
- `Set up a new board in Trello`

## Options

### Option 1: Auto-Login (Recommended)
1. Add credentials to `.env` file
2. Select app on startup (e.g., "linear")
3. Agent auto-navigates and logs in
4. Give tasks directly

### Option 2: Manual Navigation
1. Type "skip" when asked for app
2. Use `go to [URL]` to navigate anywhere
3. Login manually in browser
4. Give tasks

### Option 3: Mix Both
1. Start with auto-login for one app
2. Use `go to [URL]` to navigate to other sites later
3. Works across multiple apps in one session

## Features

✅ **Vision-Based Navigation** - Understands any web UI visually
✅ **Auto-Login** - Automatic authentication using vision AI
✅ **Multi-App Support** - Works with any web application
✅ **Natural Language** - Just describe what you want to do
✅ **Persistent Session** - Browser stays open, navigate anywhere
✅ **Smart Detection** - Finds buttons using cursor: pointer detection
✅ **20-Step Workflows** - Handles complex multi-step tasks

## Technical Details

- **Vision Model**: Claude Sonnet 4.5 (multimodal)
- **Browser**: Playwright (Chromium)
- **Detection**: Set-of-Mark (SoM) + DOM inspection
- **Max Steps**: 20 per task
- **Screenshots**: Saved to `./output/chat_session/`

## Tips

1. **Be specific** - "Create a database with 3 columns" is better than "Make a database"
2. **Navigate first** - Use "go to [URL]" before giving app-specific commands
3. **Check status** - Use `status` command to see where you are
4. **Login once** - Browser stays open, you stay logged in
5. **Multiple tasks** - Give multiple commands without restarting

## Troubleshooting

**Agent can't find a button?**
- Check if button has cursor: pointer style
- Try describing it differently
- Use `status` to verify you're on the right page

**Login failed?**
- Verify credentials in `.env` are correct
- Check app name matches exactly (lowercase)
- Login manually if auto-login fails

**Task incomplete?**
- Increase max_steps if needed (edit line 198 in chat_agent_general.py)
- Break complex tasks into smaller steps
- Check screenshots in `./output/chat_session/` to debug

## Advanced Usage

### Custom Apps

Add new apps to the registry in `chat_agent_general.py`:

```python
APP_REGISTRY = {
    "notion": "https://www.notion.so",
    "linear": "https://linear.app",
    "myapp": "https://myapp.com",  # Add your app here
}
```

Then add credentials to `.env`:
```bash
MYAPP_EMAIL=your@email.com
MYAPP_PASSWORD=yourpassword
```

### Workflow Documentation

Screenshots are automatically saved to `./output/chat_session/` - useful for:
- Debugging failed tasks
- Understanding agent behavior
- Creating documentation of workflows
