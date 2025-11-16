# Authentication Implementation Guide

## Overview

Agent B now includes comprehensive authentication support for documenting tasks on websites that require login. This enables documenting workflows in real-world applications like Linear, Notion, and other SaaS tools.

## 🔐 Features

### Automatic Login Detection
- **URL Pattern Matching**: Detects `/login`, `/signin`, `/auth` patterns
- **Form Detection**: Identifies email and password input fields
- **Smart Triggering**: Finds and clicks "Sign in" or "Log in" buttons

### Multi-Step Login Support
- **Sequential Forms**: Handles email-first, then password flows (like Google)
- **Navigation Waiting**: Waits for page transitions after login
- **Success Verification**: Confirms login succeeded before proceeding

### SPA-Specific Handling
- **Framework Detection**: Recognizes React, Vue, Angular apps
- **Loading Indicators**: Waits for spinners and skeletons to disappear
- **Animation Completion**: Ensures transitions finish before capturing
- **Modal Detection**: Identifies dialogs and overlays

## 📋 Components

### 1. AuthHandler (`src/browser/auth_handler.py`)

Handles all authentication-related operations.

**Key Methods**:

```python
async def is_login_page() -> bool
    """Detect if current page is a login page."""

async def is_logged_in() -> bool
    """Check if user is already logged in."""

async def perform_login(email: str, password: str) -> bool
    """Execute login with credentials."""

async def handle_2fa_if_present() -> bool
    """Handle 2FA if prompted (waits for manual input)."""
```

### 2. SPADetector (`src/detection/spa_detector.py`)

Enhanced detection for Single Page Applications.

**Key Methods**:

```python
async def wait_for_spa_ready() -> bool
    """Wait for SPA to fully render."""

async def detect_modal_opened() -> bool
    """Detect if a modal/dialog opened."""

async def wait_for_animation_complete()
    """Wait for CSS animations to finish."""

async def wait_for_element_stable(selector) -> bool
    """Wait for element to stop moving/changing."""
```

## 🚀 Usage

### Basic Authentication

```python
from src.main import DocumentationAgent

agent = DocumentationAgent(
    llm_provider="claude",
    model="claude-sonnet-4-20250514"
)

result = await agent.document_task(
    question="How do I create a project in Linear?",
    app_url="https://linear.app",
    credentials={
        "email": "your-email@example.com",
        "password": "your-password"
    }
)
```

### Using Environment Variables

**Recommended** for security:

```bash
# Add to .env file
LINEAR_EMAIL=your-email@example.com
LINEAR_PASSWORD=your-password
```

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

### Linear Example

```python
# Run the Linear example
python examples/linear_example.py
```

### Notion Example

```python
# Run the Notion example
python examples/notion_example.py
```

## 🔍 How It Works

### Authentication Flow

1. **Navigate to App**
   ```
   Browser → https://linear.app
   ```

2. **Check Login Status**
   ```
   AuthHandler.is_logged_in() → False
   ```

3. **Detect Login Page**
   ```
   AuthHandler.is_login_page() → True
   ```

4. **Find Login Fields**
   ```
   - Email field: input[type="email"]
   - Password field: input[type="password"]
   - Submit button: button[type="submit"]
   ```

5. **Execute Login**
   ```
   - Fill email
   - Check for multi-step (Next button)
   - Fill password
   - Click submit
   - Wait for navigation
   ```

6. **Verify Success**
   ```
   AuthHandler.is_logged_in() → True
   ```

7. **Wait for App Ready**
   ```
   SPADetector.wait_for_spa_ready()
   - Wait for loading spinners to hide
   - Wait for React/Vue to be idle
   - Wait for animations to complete
   ```

8. **Proceed with Task**
   ```
   Continue with normal task execution
   ```

## 🎯 Supported Login Patterns

### Standard Email/Password

```html
<input type="email" name="email">
<input type="password" name="password">
<button type="submit">Sign in</button>
```

✅ **Fully supported**

### Multi-Step Login (Email → Password)

```html
<!-- Step 1 -->
<input type="email" name="email">
<button>Next</button>

<!-- Step 2 (after Next) -->
<input type="password" name="password">
<button>Sign in</button>
```

✅ **Fully supported**

### SSO/OAuth (Partial Support)

```python
# Can detect and click SSO buttons
await auth_handler.handle_sso_or_oauth("google")
```

⚠️ **Experimental** - May require manual intervention

### 2FA/MFA

```python
# Waits for manual code entry
await auth_handler.handle_2fa_if_present()
```

⚠️ **Manual intervention required** - Pauses for 30 seconds

## 🛠️ Configuration

### Browser Settings

```yaml
# config/settings.yaml
browser:
  headless: false  # Set true to hide browser
  viewport:
    width: 1280
    height: 720
  timeout: 30000
```

### SPA Detection Settings

```yaml
detection:
  visual_similarity_threshold: 0.95
  dom_stability_checks: 3
  wait_between_checks: 300  # milliseconds
```

## 📝 Examples

### Linear: Create Project

```python
await agent.document_task(
    question="How do I create a new project in Linear?",
    app_url="https://linear.app",
    credentials={
        "email": os.getenv("LINEAR_EMAIL"),
        "password": os.getenv("LINEAR_PASSWORD")
    },
    output_dir="./output/linear_create_project",
    max_steps=30
)
```

### Notion: Filter Database

```python
await agent.document_task(
    question="How do I filter a database in Notion?",
    app_url="https://www.notion.so",
    credentials={
        "email": os.getenv("NOTION_EMAIL"),
        "password": os.getenv("NOTION_PASSWORD")
    },
    output_dir="./output/notion_filter_database",
    max_steps=30
)
```

### GitHub: Navigate Repository

```python
# GitHub doesn't require login for public repos
await agent.document_task(
    question="How do I navigate to the Python repository?",
    app_url="https://github.com",
    # No credentials needed
    output_dir="./output/github_navigation",
    max_steps=20
)
```

## 🔒 Security Best Practices

### 1. Use Environment Variables

❌ **Don't** hardcode credentials:
```python
credentials={"email": "user@example.com", "password": "mypassword"}
```

✅ **Do** use environment variables:
```python
credentials={
    "email": os.getenv("LINEAR_EMAIL"),
    "password": os.getenv("LINEAR_PASSWORD")
}
```

### 2. Use .env File

```bash
# .env (gitignored)
LINEAR_EMAIL=your-email@example.com
LINEAR_PASSWORD=your-password
```

### 3. Never Commit Credentials

```bash
# .gitignore already includes:
.env
.env.local
```

### 4. Use Test Accounts

- Create dedicated test accounts for automation
- Don't use your personal credentials
- Rotate passwords regularly

## 🐛 Troubleshooting

### Login Not Detected

**Symptoms**: Agent doesn't attempt login even with credentials

**Solutions**:
1. Check if page URL contains `/login` or similar
2. Verify email/password fields are visible
3. Set `headless: false` to watch browser behavior

### Login Fails

**Symptoms**: Credentials entered but login unsuccessful

**Solutions**:
1. Verify credentials are correct
2. Check for CAPTCHA (not supported)
3. Look for 2FA prompts (requires manual intervention)
4. Check browser console for errors

### SPA Not Ready

**Symptoms**: Screenshots captured before content loads

**Solutions**:
1. Increase timeouts in `config/settings.yaml`
2. Add custom wait logic for specific apps
3. Check for loading indicators not being detected

### Modal Not Detected

**Symptoms**: Missing screenshots of modal dialogs

**Solutions**:
1. Check if modal has `role="dialog"` attribute
2. Add custom modal selectors in `SPADetector`
3. Lower visual similarity threshold

## 📊 Detection Patterns

### Login Page Indicators

```javascript
// URL patterns
/login, /signin, /auth, /authenticate

// Form elements
input[type="email"]
input[type="password"]
button[type="submit"]

// Text content
"Sign in", "Log in", "Login to"
```

### Logged-In Indicators

```javascript
// User elements
.user-avatar, .user-menu, [data-testid*="user"]

// Logout buttons
button:has-text("Log out")
a:has-text("Sign out")

// Storage
localStorage: token, auth, session, user
cookies: token, session, auth
```

### SPA Loading Indicators

```javascript
// Loading spinners
.loading, .spinner, [class*="loading"]

// Skeleton screens
.skeleton, [class*="skeleton"]

// Framework-specific
[class*="Spinner"] // Linear
[class*="Loading"] // Notion
```

## 🎓 Advanced Usage

### Custom Login Detection

```python
# Extend AuthHandler for custom apps
class CustomAuthHandler(AuthHandler):
    async def is_login_page(self) -> bool:
        # Custom detection logic
        return await self.page.evaluate("""
            () => document.querySelector('.custom-login-form') !== null
        """)
```

### Custom SPA Wait Logic

```python
# Add app-specific wait conditions
await self.browser.page.evaluate("""
    () => {
        // Wait for specific app state
        return new Promise(resolve => {
            const interval = setInterval(() => {
                if (window.myApp && window.myApp.ready) {
                    clearInterval(interval);
                    resolve();
                }
            }, 100);
        });
    }
""")
```

## 📚 API Reference

### DocumentationAgent.document_task()

```python
async def document_task(
    question: str,
    app_url: str,
    credentials: Optional[Dict[str, str]] = None,
    output_dir: Optional[str] = None,
    max_steps: int = 50
) -> Dict
```

**Parameters**:
- `question`: Task to document (e.g., "How do I create a project?")
- `app_url`: Starting URL of the application
- `credentials`: Dict with `email` and `password` keys (optional)
- `output_dir`: Directory to save screenshots and guides
- `max_steps`: Maximum number of steps before timeout

**Returns**:
```python
{
    "success": bool,
    "question": str,
    "total_steps": int,
    "total_duration": str,
    "steps": [...],
    "output_directory": str,
    "guides": {
        "markdown": str,
        "json": str,
        "html": str
    }
}
```

## 🚀 Performance Tips

### 1. Adjust Max Steps

```python
# Simple tasks
max_steps=10

# Medium tasks
max_steps=25

# Complex workflows
max_steps=50
```

### 2. Tune Timeouts

```yaml
browser:
  timeout: 30000  # 30 seconds

detection:
  wait_between_checks: 300  # Decrease for faster apps
```

### 3. Use Headless Mode

```yaml
browser:
  headless: true  # Faster but can't watch
```

## ✅ Testing Checklist

Before running on production apps:

- [ ] Credentials stored in `.env` file
- [ ] `.env` file is gitignored
- [ ] Test account created (not personal)
- [ ] Browser set to `headless: false` for first run
- [ ] Max steps appropriate for task complexity
- [ ] Output directory writable
- [ ] API keys configured

---

**Authentication implementation complete!** 🔐

You can now document tasks in any web application that requires login.

For questions or issues, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md) or open a GitHub issue.
