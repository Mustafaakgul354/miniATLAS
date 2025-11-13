# mini-Atlas Desktop Application UI Overview

## Application Interface

The desktop application provides a clean, intuitive interface divided into several sections:

```
┌────────────────────────────────────────────────────────────────────────┐
│ 🤖 mini-Atlas Browser Agent               [✓ Backend Connected]        │
├────────────────────────────────────────────────────────────────────────┤
│ [https://www.google.com                    ] [Go] [Summarize Page]     │
├────────────────────────────────────────────────────────────────────────┤
│ [Enter task: "Search for Playwright..."                ] [Execute Task]│
├───────────────────────────┬────────────────────────────────────────────┤
│ Agent Status              │ Browser View               [Refresh Status]│
│                           │                                            │
│ Session ID: sess_abc123   │ ┌──────────────────────────────────────┐  │
│ Status: Running           │ │                                      │  │
│ Current URL: google.com   │ │    [Screenshot of browser page]      │  │
│ Steps: 3                  │ │                                      │  │
│                           │ │                                      │  │
│ ┌─────────────────────┐   │ └──────────────────────────────────────┘  │
│ │ Page Summary        │   │                                            │
│ │                     │   │ Action History                             │
│ │ This page shows...  │   │ ┌──────────────────────────────────────┐  │
│ └─────────────────────┘   │ │ CLICK                                │  │
│                           │ │ Clicked search button                │  │
│ Agent Reasoning           │ │ Result: Success                      │  │
│ ┌─────────────────────┐   │ │ Step 3 • 14:23:45                    │  │
│ │ Step 3: Executing   │   │ ├──────────────────────────────────────┤  │
│ │ search to find      │   │ │ FILL                                 │  │
│ │ relevant results    │   │ │ Typed into search field              │  │
│ └─────────────────────┘   │ │ Result: Success                      │  │
│                           │ │ Step 2 • 14:23:43                    │  │
└───────────────────────────┴────────────────────────────────────────────┘
│ Ready                                                                  │
└────────────────────────────────────────────────────────────────────────┘
```

## UI Components

### Header Bar
- **Application Title**: "🤖 mini-Atlas Browser Agent"
- **Backend Status**: Shows connection status with Python backend
  - Green: "✓ Backend Connected"
  - Red: "✗ Backend Disconnected"

### Navigation Bar (Phase 1)
- **URL Input**: Text field for entering website addresses
  - Placeholder: "Enter URL (e.g., https://www.google.com)"
  - Auto-adds https:// if missing
- **Go Button**: Navigates to the entered URL
- **Summarize Page Button**: Analyzes current page with AI (Phase 2)

### Task Bar (Phase 3)
- **Task Input**: Natural language input for AI agent tasks
  - Placeholder: "Enter task in natural language..."
  - Example: "Search for Playwright automation and click the first result"
- **Execute Task Button**: Starts the AI agent with the given task

### Left Panel - Agent Status

#### Session Information
- **Session ID**: Unique identifier for current automation session
- **Status**: Current state (Idle, Running, Completed, Failed)
- **Current URL**: The webpage currently being viewed
- **Steps**: Number of actions taken

#### Page Summary (Phase 2)
- Displays AI-generated summary of the current webpage
- Shows after clicking "Summarize Page"
- Collapsible section

#### Agent Reasoning
- Real-time display of agent's thought process
- Shows why the agent is taking each action
- Updates as the agent works

### Right Panel - Browser View

#### Screenshot Display
- Live screenshot of the browser page
- Updates after each agent action
- Click to view full size

#### Action History
- Chronological list of all actions taken
- Each action shows:
  - Action type (CLICK, FILL, NAVIGATE, etc.)
  - Description of what was done
  - Result (Success/Failed)
  - Error messages if any
  - Timestamp
- Color-coded:
  - Green border: Successful actions
  - Red border/background: Failed actions

#### Refresh Button
- Manually refresh the current status
- Useful when automatic updates are delayed

### Status Bar
- Bottom bar showing current operation status
- Examples:
  - "Ready"
  - "Navigating to https://example.com..."
  - "Agent is working..."
  - "Task completed successfully"

## Color Scheme

- **Primary Color**: Purple gradient (#667eea to #764ba2)
- **Success**: Green (#10b981)
- **Warning**: Yellow/Amber (#fbbf24)
- **Error**: Red (#ef4444)
- **Background**: Light gray (#f5f5f5)
- **Text**: Dark gray (#1f2937)

## Interactions

### Phase 1: Basic Navigation
1. User enters URL
2. Clicks "Go" or presses Enter
3. Backend navigates to the page
4. Status updates show progress
5. Screenshot appears when loaded

### Phase 2: Page Summarization
1. User navigates to a page
2. Clicks "Summarize Page"
3. Loading spinner shows
4. AI analyzes the page
5. Summary appears in left panel

### Phase 3: Task Execution
1. User navigates to starting page
2. Enters natural language task
3. Clicks "Execute Task" or presses Enter
4. Real-time updates:
   - Reasoning shows agent's thoughts
   - Action history populates
   - Screenshots update
   - Step count increments
5. Task completes or fails
6. Final status shown

## Automatic Updates

When a session is active:
- Status updates every 2 seconds
- Screenshots refresh automatically
- Action history updates in real-time
- Step count increments
- No manual refresh needed

## Responsive Design

- Minimum width: 1400px
- Minimum height: 900px
- Left panel: Fixed 400px width
- Right panel: Flexible, takes remaining space
- Scrollable panels for long content

## Keyboard Shortcuts

- **Enter in URL field**: Navigate to URL
- **Enter in Task field**: Execute task
- **F12 (in dev mode)**: Open DevTools

## States

### Idle State
- No active session
- Session ID: "None"
- Status: "Idle"
- Placeholder messages in panels

### Running State
- Session active
- Status: "Running"
- Loading spinner visible
- Updates every 2 seconds

### Completed State
- Session finished successfully
- Status: "Completed"
- Final screenshot and actions shown
- No more updates

### Failed State
- Session encountered error
- Status: "Failed"
- Error messages in action history
- Last known state shown

### Waiting State
- Session paused (e.g., CAPTCHA)
- Status: "Waiting for human"
- User intervention needed
- "Continue" option available (backend)

## Accessibility

- Clear visual hierarchy
- Color-coded status indicators
- Descriptive button labels
- Error messages in plain language
- Loading states clearly indicated

## Future Enhancements

Possible additions:
- Dark mode toggle
- Session history sidebar
- Export session data
- Keyboard shortcuts panel
- Settings panel for configuration
- Multi-tab support
- Session save/restore
