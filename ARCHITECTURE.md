# Agent B - Architecture Documentation

## System Architecture

Agent B is a multi-component system designed for autonomous web task documentation using vision-based AI.

## High-Level Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                      Agent B System                          │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              DocumentationAgent                         │ │
│  │              (Main Orchestrator)                        │ │
│  └─────────────────┬────────────────────────────────────┬─┘ │
│                    │                                     │   │
│         ┌──────────▼──────────┐              ┌──────────▼───▼──────┐
│         │   VisionWebAgent    │              │  BrowserController   │
│         │   (Decision Making) │              │   (Automation)       │
│         │                     │              │                      │
│         │  • Claude API       │◄────────────►│  • Playwright        │
│         │  • Prompt Engine    │   Screenshots│  • SoMMarker         │
│         │  • Action Parser    │   + State    │  • ActionExecutor    │
│         └─────────────────────┘              └──────────────────────┘
│                    │                                     │
│         ┌──────────▼──────────┐              ┌──────────▼───────────┐
│         │   StateDetector     │              │  ScreenshotManager   │
│         │                     │              │                      │
│         │  • Visual Diff      │              │  • Capture Logic     │
│         │  • DOM Tracking     │              │  • Metadata Storage  │
│         │  • Change Detection │              │  • Step Counter      │
│         └─────────────────────┘              └──────────┬───────────┘
│                                                         │
│                                              ┌──────────▼───────────┐
│                                              │   GuideGenerator     │
│                                              │                      │
│                                              │  • Markdown Output   │
│                                              │  • HTML Output       │
│                                              │  • JSON Output       │
│                                              └──────────────────────┘
└──────────────────────────────────────────────────────────────────────┘
```

## Component Breakdown

### 1. DocumentationAgent (Main Orchestrator)

**Location**: `src/main.py`

**Responsibility**: Coordinates all components and manages the task execution lifecycle.

**Key Methods**:
```python
async def document_task(
    question: str,
    app_url: str,
    credentials: Optional[Dict] = None,
    output_dir: Optional[str] = None,
    max_steps: int = 50
) -> Dict
```

**Flow**:
1. Initialize all components (browser, agent, detectors)
2. Navigate to starting URL
3. Run main agent loop:
   - Capture current state
   - Get decision from VisionWebAgent
   - Execute action via BrowserController
   - Capture screenshot if needed
   - Check for completion
4. Generate guides in multiple formats
5. Return results

### 2. VisionWebAgent (AI Decision Engine)

**Location**: `src/agent/vision_agent.py`

**Responsibility**: Uses vision LLM to understand UI and decide actions.

**Key Methods**:
```python
def decide_next_action(
    goal: str,
    current_state: PageState,
    screenshot_path: str
) -> AgentResponse
```

**Process**:
1. Build multi-modal prompt (screenshot + accessibility tree + context)
2. Call Claude/GPT-4o API
3. Parse JSON response into AgentAction
4. Return structured decision

**Prompt Strategy**:
- System prompt defines agent role and output format
- Task prompt includes current state and goal
- Few-shot examples guide behavior
- Structured JSON output ensures parsability

### 3. BrowserController (Automation Layer)

**Location**: `src/browser/controller.py`

**Responsibility**: Manages browser lifecycle and page interaction.

**Key Methods**:
```python
async def start()  # Launch browser
async def navigate(url: str)  # Navigate to URL
async def get_current_state() -> PageState  # Capture state
async def execute_action(action: AgentAction) -> bool  # Execute action
async def wait_for_stability() -> bool  # Wait for UI stability
async def stop()  # Cleanup
```

**Integration Points**:
- Uses Playwright for browser automation
- Integrates SoMMarker for element identification
- Uses ActionExecutor for action execution

### 4. SoMMarker (Set-of-Mark Implementation)

**Location**: `src/browser/som_marker.py`

**Responsibility**: Overlays numbered markers on interactive elements.

**Key Methods**:
```python
async def mark_page(page) -> List[dict]  # Mark all interactive elements
async def remove_markers(page)  # Clean up markers
async def highlight_element(page, marker_id: int)  # Visual feedback
```

**Implementation**:
```javascript
// Injected JavaScript
1. Query all interactive elements (buttons, links, inputs, etc.)
2. Filter for visible elements
3. Create numbered div overlays
4. Position at element coordinates
5. Return element metadata
```

**Element Selection**:
- `button`, `a[href]`, `input`, `textarea`, `select`
- `[role="button"]`, `[role="link"]`, `[role="tab"]`
- `[onclick]`, `[contenteditable]`

### 5. ActionExecutor (Action Implementation)

**Location**: `src/browser/action_executor.py`

**Responsibility**: Translates AgentActions into browser operations.

**Supported Actions**:
- **click**: Click element by marker ID
- **type**: Type text into input field
- **navigate**: Go to URL
- **wait**: Wait for UI stability
- **scroll**: Scroll page up/down
- **done**: Mark task complete

**Click Implementation**:
```python
1. Parse marker ID from target (e.g., "[15]")
2. Highlight element for visual feedback
3. Execute click via JavaScript
4. Wait briefly for any triggered changes
```

### 6. StateDetector (UI Change Detection)

**Location**: `src/detection/state_detector.py`

**Responsibility**: Determines when UI changes warrant screenshot capture.

**Detection Methods**:

1. **Visual Similarity (SSIM)**:
   ```python
   - Load current and previous screenshots
   - Convert to grayscale
   - Calculate structural similarity index
   - Threshold: 0.95 (95% similar = no significant change)
   ```

2. **DOM Hash Comparison**:
   ```python
   - Hash page DOM content
   - Compare with previous hash
   - Detects structural changes even without visual difference
   ```

3. **Action-Based Heuristics**:
   ```python
   - Always capture for: click, navigate, done
   - Never capture for: wait, minor hover
   - Conditional for: type (only after form submit)
   ```

### 7. ScreenshotManager (Screenshot Storage)

**Location**: `src/screenshot/manager.py`

**Responsibility**: Manages screenshot collection and metadata.

**Data Model**:
```python
@dataclass
class ScreenshotRecord:
    path: str                    # File path
    description: str             # Human-readable description
    action_type: str            # Action that triggered it
    timestamp: float            # When captured
    element_target: Optional[str]  # Target element
    step_number: int            # Sequential step number
```

**Key Features**:
- Auto-incrementing step counter
- Rich metadata storage
- Chronological ordering
- Query by step number

### 8. GuideGenerator (Output Generation)

**Location**: `src/screenshot/guide_generator.py`

**Responsibility**: Converts screenshot sequence into documentation.

**Output Formats**:

1. **Markdown**:
   - Simple text format
   - Embedded images via relative paths
   - Good for GitHub, documentation sites

2. **HTML**:
   - Styled, professional appearance
   - Embedded CSS
   - Interactive viewing in browser

3. **JSON**:
   - Structured data
   - Machine-readable
   - Easy integration with other systems

## Data Flow

### Complete Task Execution Flow

```
1. User Request
   ├─ question: "How do I create a project?"
   └─ app_url: "https://linear.app"

2. Initialization
   ├─ Start browser (Playwright)
   ├─ Initialize VisionAgent (Claude API)
   ├─ Create output directory
   └─ Set up detectors and managers

3. Navigation
   ├─ Navigate to app_url
   ├─ Wait for page load
   └─ Wait for UI stability

4. Main Loop (repeat until done or max_steps)
   │
   ├─ 4a. Capture State
   │   ├─ Mark page with SoM
   │   ├─ Take screenshot
   │   ├─ Extract element info
   │   └─ Calculate DOM hash
   │
   ├─ 4b. AI Decision
   │   ├─ Build multi-modal prompt
   │   ├─ Call Claude API
   │   ├─ Parse JSON response
   │   └─ Get AgentAction
   │
   ├─ 4c. Screenshot Decision
   │   ├─ Check action.should_capture_screenshot
   │   ├─ Run StateDetector checks
   │   └─ Save if significant change
   │
   ├─ 4d. Execute Action
   │   ├─ Map action to browser command
   │   ├─ Execute via ActionExecutor
   │   └─ Handle errors
   │
   ├─ 4e. Wait for Stability
   │   ├─ Monitor DOM changes
   │   ├─ Wait for network idle
   │   └─ Confirm UI stable
   │
   └─ 4f. Check Completion
       ├─ action_type == "done"?
       ├─ Step count >= max_steps?
       └─ Continue or exit

5. Guide Generation
   ├─ Collect all ScreenshotRecords
   ├─ Generate Markdown guide
   ├─ Generate HTML guide
   ├─ Generate JSON guide
   └─ Save to output directory

6. Cleanup
   ├─ Close browser
   ├─ Return results
   └─ Log summary
```

## Key Design Patterns

### 1. Multi-Modal Perception

Combines multiple information sources:
- **Visual**: Screenshot with markers
- **Structural**: Accessibility tree (elements, roles, labels)
- **Contextual**: URL, title, history

This redundancy improves accuracy and robustness.

### 2. Separation of Concerns

Each component has a single, clear responsibility:
- BrowserController: Browser management only
- VisionAgent: Decision making only
- StateDetector: Change detection only
- etc.

### 3. Async/Await Pattern

All I/O operations are asynchronous:
- Browser actions
- API calls
- File I/O

Enables efficient concurrent operations.

### 4. Configuration-Driven Behavior

Settings in `config/settings.yaml` control:
- Browser behavior
- Detection thresholds
- LLM parameters
- Output formatting

Easy to tune without code changes.

### 5. Error Handling Strategy

- **Browser errors**: Retry with timeout
- **LLM parsing errors**: Fallback to wait action
- **Action failures**: Log and continue
- **Stability timeouts**: Proceed anyway (non-critical)

## Performance Considerations

### Token Optimization

**Problem**: Each LLM call costs tokens

**Solutions**:
1. Limit element list to first 50 interactive elements
2. Truncate action history to last 10 actions
3. Compress element text to 100 chars
4. Use efficient prompt templates

### Screenshot Efficiency

**Problem**: Too many screenshots = slow + large output

**Solutions**:
1. StateDetector filters redundant captures
2. SSIM threshold prevents near-duplicates
3. Agent decides when screenshots add value
4. Milestone actions (click, navigate) always captured

### Browser Performance

**Problem**: Page loads and stability checks take time

**Solutions**:
1. Parallel operations where possible
2. Configurable timeouts
3. Progressive stability checks (3 samples)
4. Network idle detection with timeout

## Extension Points

### Adding New LLM Providers

Implement in `VisionWebAgent._call_<provider>()`:

```python
def _call_gemini(self, prompt: str, screenshot_b64: str) -> str:
    # Implement Gemini API call
    pass
```

### Adding New Action Types

1. Add to `AgentAction.action_type` enum in `schemas.py`
2. Implement in `ActionExecutor._execute_<action>()`
3. Update prompts to describe new action

### Custom Output Formats

Implement in `GuideGenerator`:

```python
def generate_pdf(self, screenshots, task_goal, output_path):
    # Generate PDF guide
    pass
```

### Custom State Detection

Extend `StateDetector`:

```python
def has_modal_opened(self, page) -> bool:
    # Custom logic to detect modal
    return await page.evaluate("...")
```

## Security Considerations

1. **Credentials**: Never log or store credentials
2. **Secrets**: Use environment variables for API keys
3. **Sandboxing**: Browser runs in isolated context
4. **Input Validation**: Sanitize URLs and user input
5. **API Keys**: Never commit to version control

## Testing Strategy

### Unit Tests
- Component initialization
- Configuration loading
- Data schema validation

### Integration Tests
- Browser automation
- SoM marker injection
- Screenshot capture

### End-to-End Tests
- Full task execution
- Guide generation
- Multiple output formats

## Future Enhancements

1. **Login Automation**: Generic login flow detection
2. **Error Recovery**: Self-healing when actions fail
3. **Multi-Tab Support**: Handle pop-ups and new tabs
4. **Video Recording**: Capture full session as video
5. **Parallel Tasks**: Document multiple tasks simultaneously
6. **State Persistence**: Resume interrupted tasks
7. **Interactive Mode**: Human-in-the-loop corrections

---

**Architecture designed for: Modularity, Extensibility, Reliability**
