# UI Overview - mini-Atlas Desktop

Interface documentation for Electron desktop application.

## Layout

### Top Bar
- **Logo**: mini-Atlas branding
- **Address Bar**: URL/task input field
- **Go Button**: Start navigation or task execution
- **Summarize Button**: Start page summarization
- **Stop Button**: Stop active session (shown when session active)
- **Status Indicator**: Current session status with colored dot

### Main Content (2-Panel Layout)

#### Left Panel: Browser View
- **Header**: "Browser View" title + current URL
- **Content**: 
  - Screenshot display (when session active)
  - Empty state (when no session)
  - Loading state (during execution)

#### Right Panel: Agent Activity
- **Header**: "Agent Activity" title + step counter
- **Content**:
  - Step-by-step agent actions
  - Reasoning for each step
  - Action details (type, selector, value)
  - Results (success/error indicators)
  - Timestamps

### Bottom Status Bar
- **Backend Status**: Connection indicator (Connected/Disconnected)
- **Session ID**: Current session identifier
- **Mode**: Active mode (Navigation/Summarization/Task Execution)

## User Interactions

### Navigation (Phase 1)

1. **Enter URL** in address bar
2. **Click "Go"** button
3. **Watch** real-time screenshot updates
4. **View** navigation steps in activity panel

**UI Updates:**
- Status dot: Green (running) → Blue (completed)
- Browser view: Shows page screenshot
- Activity panel: Shows navigation steps
- Status bar: Displays session ID

### Summarization (Phase 2)

1. **Enter URL** in address bar
2. **Click "Summarize"** button
3. **Wait** for multi-step execution
4. **Read** summary in activity panel

**UI Updates:**
- Status: "Summarizing page..."
- Activity panel: Shows reasoning steps
- Final step: Contains summary text

### Task Execution (Phase 3)

1. **Enter task** in address bar (e.g., "Search for Playwright and click first result")
2. **Click "Go"** button
3. **Watch** agent execute multi-step workflow
4. **Monitor** real-time updates

**UI Updates:**
- Status: "Executing task..."
- Browser view: Screenshots update after each action
- Activity panel: Shows all steps with reasoning
- Step counter: Increments in real-time

## Status Indicators

### Status Dot Colors
- **Gray**: Ready/Idle
- **Green**: Running (pulsing animation)
- **Blue**: Completed
- **Red**: Failed

### Backend Status
- **Green "Connected"**: Backend reachable
- **Red "Disconnected"**: Backend unreachable
- **Red "Error"**: Connection error

## Visual Elements

### Screenshots
- Full-width display in browser view
- Updates every 2 seconds during execution
- Maintains aspect ratio
- White background for contrast

### Step Items
- Dark background (#2a2a2a)
- Border highlight on hover
- Step number in purple (#667eea)
- Timestamp in gray
- Reasoning in italic gray
- Action details in monospace font
- Results with color coding (green/red)

### Buttons
- **Primary (Go)**: Purple gradient
- **Secondary (Summarize)**: Dark gray
- **Danger (Stop)**: Red
- Hover effects: Slight lift and opacity change
- Disabled state: Reduced opacity

## Keyboard Shortcuts

- **Enter**: Submit address bar (same as "Go" button)
- **Escape**: (Future: Cancel/stop current operation)

## Responsive Behavior

- **Window Resize**: Panels adjust proportionally
- **Small Window**: Minimum width enforced
- **Full Screen**: (Future: Full screen mode support)

## Error States

### Backend Disconnected
- Status bar shows "Disconnected" in red
- Buttons disabled
- Error message on action attempt

### Session Failed
- Status dot: Red
- Status text: "Failed"
- Error message in activity panel
- Last step shows error details

### Network Error
- Error message displayed
- UI remains functional
- Can retry operation

## Loading States

### Session Starting
- Status: "Starting..."
- Buttons: Disabled
- Screenshot: Loading placeholder

### Session Running
- Status: "Running"
- Status dot: Pulsing green
- Screenshot: Updates every 2s
- Steps: Appear in real-time

### Session Complete
- Status: "Completed"
- Status dot: Blue
- Final screenshot: Displayed
- All steps: Visible in activity panel

## Accessibility

- **Keyboard Navigation**: Tab through interactive elements
- **Screen Reader**: (Future: ARIA labels)
- **High Contrast**: (Future: Theme options)
- **Font Scaling**: Browser default scaling supported

## Color Scheme

- **Background**: Dark (#0a0a0a)
- **Panels**: White (left) / Dark (right)
- **Primary**: Purple gradient (#667eea → #764ba2)
- **Success**: Green (#4caf50)
- **Error**: Red (#f44336)
- **Text**: White (dark bg) / Black (light bg)
- **Muted**: Gray (#666, #999)

## Future Enhancements

- Session history sidebar
- Screenshot gallery view
- Export session data
- Custom theme selection
- Keyboard shortcut customization
- Full screen mode
- Multi-session support

