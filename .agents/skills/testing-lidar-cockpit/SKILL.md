# Testing LiDAR Control Cockpit

## Dev Server Setup

### Backend
```bash
cd /home/ubuntu/repos/lidar-scan
uv sync
uv run uvicorn app.app:app --host 0.0.0.0 --port 8005
```
Wait for `Uvicorn running on http://0.0.0.0:8005` and confirm module registries loaded (look for `Loaded module registry: detection`, etc.).

### Frontend
```bash
cd /home/ubuntu/repos/lidar-scan/web
npx ng serve --port 4200 --host 0.0.0.0
```
Wait for `Application bundle generation complete` and the local URL.

## UI Testing Patterns

### Flow Canvas (Settings Page)
- Navigate to `http://localhost:4200/settings`
- The left palette shows node categories (application, calibration, detection, flow_control, fusion, operation, sensor)
- Each category contains draggable node cards

### Adding Nodes to Canvas
HTML5 drag-and-drop from the palette may not work reliably with automated screen interaction tools. Use JavaScript dispatch as a workaround:

```javascript
// 1. Find the palette item and drop target
const paletteItems = document.querySelectorAll('app-flow-canvas-palette [draggable="true"]');
let targetItem = null;
paletteItems.forEach(item => {
  if (item.textContent.includes('TARGET_NODE_NAME')) targetItem = item;
});

const flowCanvas = document.querySelector('app-flow-canvas');
const allDivs = flowCanvas.querySelectorAll('div');
let dropTarget = null;
for (const div of allDivs) {
  if (div.className && div.className.includes('absolute') && div.className.includes('inset-0')) {
    dropTarget = div.firstElementChild;
    break;
  }
}

// 2. Dispatch drag events
if (targetItem && dropTarget) {
  const dt1 = new DataTransfer();
  dt1.setData('text/plain', 'NODE_TYPE_ID');
  targetItem.dispatchEvent(new DragEvent('dragstart', { bubbles: true, cancelable: true, dataTransfer: dt1 }));

  const rect = dropTarget.getBoundingClientRect();
  dropTarget.dispatchEvent(new DragEvent('dragover', {
    bubbles: true, cancelable: true,
    clientX: rect.left + 300, clientY: rect.top + 200,
    dataTransfer: new DataTransfer()
  }));

  dropTarget.dispatchEvent(new DragEvent('drop', {
    bubbles: true, cancelable: true,
    clientX: rect.left + 300, clientY: rect.top + 200,
    dataTransfer: new DataTransfer()
  }));
}
```

Replace `TARGET_NODE_NAME` with the display name (e.g., "3D Object Detection") and `NODE_TYPE_ID` with the backend type (e.g., "object_detection_3d").

### Testing Node Editors
1. After adding a node, the editor drawer opens automatically on the right
2. Verify all properties from the backend `NodeDefinition.properties` render as correct input types:
   - `type: "select"` → `syn-select` dropdown
   - `type: "number"` → `syn-input type="number"` with +/- steppers
   - `type: "boolean"` → `syn-checkbox`
   - `type: "string"` → `syn-input type="text"`
3. Check default values match the backend `PropertySchema.default`
4. Modify a value, click Save, verify toast notification appears
5. Double-click the node on canvas to re-open editor and verify value persisted

### Testing Save Flow
- Save stages changes locally (toast: "Node X staged for save")
- Status bar shows "Unsaved" indicator
- Click "Apply" to push changes to the backend
- Click "Sync" to pull latest config from backend

## Key Routes
- `/start` — Dashboard
- `/settings` — Flow canvas with node palette and editor
- `/workspaces` — Workspace management
- `/calibration` — Sensor calibration
- `/recordings` — Recording viewer
- `/models` — ML model checkpoint management
- `/logs` — System logs

## Backend API Verification
- `GET /api/v1/nodes/definitions` — Returns all registered node definitions with properties
- Verify detection module loads: check backend logs for `Loaded module registry: detection`

## Known Issues
- The detection backend module might not exist on all branches. If testing the detection editor, ensure the `app/modules/detection/` directory exists with `registry.py`. You may need to merge the detection branch locally.
- `window.ng` is not available in production builds, so you cannot access Angular component instances directly from the console.

## Devin Secrets Needed
No secrets required for local testing. Backend and frontend run without authentication.
