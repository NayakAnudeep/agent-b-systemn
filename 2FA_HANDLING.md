# 2FA/MFA & Email Verification Handling in Agent B

Agent B automatically detects and handles two-factor authentication (2FA) and email verification during login!

## How It Works

### 1. **Automatic Detection**
When logging in, the agent detects verification pages by looking for keywords:
- **2FA/MFA**: "two-factor", "2fa", "verification code", "authenticator", "security code", "6-digit code"
- **Email Verification**: "check your email", "email verification", "sent you a link", "magic link", "verify your email"
- And more...

### 2. **Pause for Human**
When 2FA is detected, the agent:
1. ⏸️  **Pauses** automation
2. 📱 **Shows clear message** telling you to complete 2FA
3. ⏱️  **Waits** up to 5 minutes (300 seconds)
4. 👀 **Monitors** page state every 2 seconds

### 3. **Auto-Resume**
Once you complete 2FA:
- Agent detects the page state change (URL or content changed)
- ✅ Automatically resumes authentication
- Continues with the login process

## Example Flow

### Without 2FA (Normal Login)
```
💬 You: Create a project in github

✅ Detected app: github (your@email.com)
⏳ Starting browser...
⏳ Navigating to github...
⏳ Logging in as your@email.com...
✅ Successfully logged in to github!

🔄 Executing: Create a project in github
```

### With 2FA (GitHub, etc.)
```
💬 You: Create a project in github

✅ Detected app: github (your@email.com)
⏳ Starting browser...
⏳ Navigating to github...
⏳ Logging in as your@email.com...

🔐 2FA detected (keyword: 'authentication code')

======================================================================
🔐 VERIFICATION REQUIRED (2FA / EMAIL)
======================================================================

⏸️  The agent has detected a verification page.
📱 Please complete the verification manually in the browser:
   • Check your email and click the verification link
   • Enter your authentication code
   • Complete SMS verification
   • Approve the login on your device

💡 The agent will automatically resume once you complete verification.
⏱️  Waiting up to 300 seconds...
======================================================================

⏳ Still waiting... (290s remaining)
⏳ Still waiting... (280s remaining)
⏳ Still waiting... (270s remaining)

✅ 2FA completed! Resuming automation...
----------------------------------------------------------------------

✅ Successfully logged in to github!

🔄 Executing: Create a project in github
```

### With Email Verification (Linear, etc.)
```
💬 You: Create a new project in linear

✅ Detected app: linear (your@email.com)
⏳ Starting browser...
⏳ Navigating to linear...
⏳ Logging in as your@email.com...

🔐 Email verification detected (keyword: 'check your email')

======================================================================
🔐 VERIFICATION REQUIRED (2FA / EMAIL)
======================================================================

⏸️  The agent has detected a verification page.
📱 Please complete the verification manually in the browser:
   • Check your email and click the verification link
   • Enter your authentication code
   • Complete SMS verification
   • Approve the login on your device

💡 The agent will automatically resume once you complete verification.
⏱️  Waiting up to 300 seconds...
======================================================================

⏳ Still waiting... (290s remaining)
⏳ Still waiting... (280s remaining)

✅ Email verification completed! Resuming automation...
----------------------------------------------------------------------

✅ Successfully logged in to linear!

🔄 Executing: Create a new project in linear
```

## Supported Verification Methods

The agent pauses for ANY verification method:
- ✅ **Email magic links** (Linear, Slack, etc.)
- ✅ **Email verification codes**
- ✅ **Authenticator apps** (Google Authenticator, Authy, etc.)
- ✅ **SMS codes**
- ✅ **Push notifications** (approve on phone)
- ✅ **Backup codes**
- ✅ **Hardware keys** (YubiKey, etc.)

## Settings

### Change Timeout
Default: 5 minutes (300 seconds)

To change, edit `chat_agent_general.py`:
```python
success = await auth_handler.authenticate(
    credentials=self.credentials,
    screenshot_dir="./output/chat_session"
)
```

Or in `auth_handler.py`, modify:
```python
success = await self.wait_for_human_intervention(max_wait_seconds=600)  # 10 minutes
```

### Detection Keywords
To add more 2FA keywords, edit `auth_handler.py`:
```python
self.twofa_keywords = [
    "two-factor", "2fa", "two factor", "2-factor",
    "verification code", "authenticator", "security code",
    "6-digit", "authentication code", "verify your identity",
    "enter code", "verification", "multi-factor",
    "your-custom-keyword"  # Add here
]
```

## How State Detection Works

The agent monitors two things:

1. **URL Change**
   - Before: `https://github.com/login/two_factor`
   - After: `https://github.com/dashboard` (2FA completed!)

2. **Page Content Change**
   - Calculates MD5 hash of URL + first 500 chars of content
   - If hash changes = user completed 2FA
   - Resumes automation

## Timeout Behavior

If you don't complete 2FA within the timeout (5 minutes):
```
⚠️  Timeout after 300 seconds
❌ 2FA timeout or failed
❌ Failed to login to github
```

You can:
- Restart the agent
- Try again
- Or login manually in the browser

## Apps Known to Use Verification

- ✅ **Linear** - Email magic link (passwordless login)
- ✅ **Slack** - Email magic link or SMS/authenticator
- ✅ **GitHub** - Authenticator app or SMS
- ✅ **Google/Gmail** - Authenticator app or SMS
- ✅ **Microsoft/Outlook** - Authenticator app or SMS
- ✅ **Dropbox** - Authenticator app or SMS
- ✅ **AWS** - MFA device
- ⚠️ **Notion** - Usually no 2FA for personal accounts

## Benefits

1. **Seamless UX** - No need to disable 2FA for automation
2. **Secure** - Keeps 2FA enabled on your accounts
3. **Automatic** - Agent handles detection and resume
4. **Universal** - Works with any 2FA method
5. **Clear Feedback** - Shows exactly what to do

## Technical Implementation

- **Detection**: Keyword matching in page content, title, and URL
- **Monitoring**: State hashing (URL + content)
- **Polling**: Checks every 2 seconds
- **Progress**: Updates every 10 seconds
- **Timeout**: Configurable (default 300s)

## Example Code

```python
# In authenticate() method after login form submission:
if await self._detect_2fa_page():
    logger.info("🔐 2FA page detected - waiting for human intervention")
    success = await self.wait_for_human_intervention(max_wait_seconds=300)
    if success:
        logger.info("✅ User completed 2FA - continuing authentication check")
    else:
        logger.error("❌ 2FA timeout or failed")
        return False
```

## FAQ

**Q: What if my app has a different 2FA page?**
A: Add the keyword to `twofa_keywords` list in `auth_handler.py`

**Q: Can I skip 2FA detection?**
A: Yes, just comment out the 2FA check in the authenticate() method

**Q: What if it doesn't detect my 2FA page?**
A: Add keywords from your 2FA page to the detection list

**Q: Can I use this with hardware keys?**
A: Yes! Agent pauses and waits for you to use your YubiKey/other hardware

**Q: Will it work with biometric 2FA?**
A: Yes! Any 2FA method that causes a page state change will work
