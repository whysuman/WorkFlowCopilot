# Power Apps Integration Guide

This guide explains how to connect a Power Apps canvas app to the Manufacturing Investigation Copilot FastAPI backend.

## Prerequisites

- FastAPI server running (`uv run uvicorn api.main:app --port 8000`)
- Power Apps maker environment with custom connector access

## 1. Custom Connector Setup

1. Start the API locally and download the OpenAPI spec:
   ```
   curl http://localhost:8000/openapi.json -o openapi.json
   ```

2. In the Power Apps maker portal:
   - Go to **Data** > **Custom Connectors** > **New custom connector** > **Import an OpenAPI file**
   - Upload `openapi.json`
   - Set the host to your server URL (e.g., `localhost:8000` for dev)
   - Save and test the connector

## 2. Canvas App Architecture (3 Screens)

### Screen 1: Intake

Dropdowns populated from the `/config` endpoint, metric inputs, and a Submit button.

```
// On app start — load dropdown options
ClearCollect(
    colConfig,
    CopilotAPI.GetConfig()
);

// Populate dropdowns
Dropdown_Site.Items = colConfig.sites
Dropdown_ToolGroup.Items = colConfig.tool_groups
Dropdown_ProcessStep.Items = colConfig.process_steps
Dropdown_Severity.Items = colConfig.severity_levels
```

Submit button calls `/investigate`:

```
// On Submit button click
Set(
    varResponse,
    CopilotAPI.Investigate({
        site: Dropdown_Site.Selected.Value,
        tool_group: Dropdown_ToolGroup.Selected.Value,
        process_step: Dropdown_ProcessStep.Selected.Value,
        severity: Dropdown_Severity.Selected.Value,
        anomaly_summary: TextInput_Summary.Text,
        metrics: {
            yield_pct: Value(TextInput_Yield.Text),
            affected_lot_count: Value(TextInput_Lots.Text),
            time_window_hours: Value(TextInput_Hours.Text),
            metric_variance: Value(TextInput_Variance.Text),
            change_magnitude: Value(TextInput_ChangeMag.Text),
            measurement_confidence: Value(TextInput_MeasConf.Text),
            rework_rate: Value(TextInput_Rework.Text)
        }
    })
);
Navigate(Screen_Results);
```

### Screen 2: Results

Displays the investigation response.

- **Assessment card**: `varResponse.assessment.pattern`, `.priority`, `.confidence`
- **Similar Cases gallery**: `varResponse.similar_cases` as Items
- **Next Checks list**: `varResponse.next_checks` as Items
- **Narrative text**: `varResponse.narrative`
- **Escalation summary**: `varResponse.escalation_summary`

### Screen 3: NLP Mode

Free-text input that calls `/extract`, shows extracted fields for review, then submits to `/investigate`.

```
// Extract button
Set(
    varExtracted,
    CopilotAPI.Extract({ text: TextInput_FreeText.Text })
);

// After review, submit extracted fields
Set(
    varResponse,
    CopilotAPI.Investigate({
        site: varExtracted.site,
        tool_group: varExtracted.tool_group,
        process_step: varExtracted.process_step,
        severity: varExtracted.severity,
        anomaly_summary: varExtracted.anomaly_summary,
        metrics: {
            yield_pct: varExtracted.yield_pct,
            affected_lot_count: varExtracted.affected_lot_count,
            time_window_hours: varExtracted.time_window_hours,
            metric_variance: varExtracted.metric_variance,
            change_magnitude: varExtracted.change_magnitude,
            measurement_confidence: varExtracted.measurement_confidence,
            rework_rate: varExtracted.rework_rate
        }
    })
);
Navigate(Screen_Results);
```

## 3. API Endpoints Summary

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/investigate` | POST | Full investigation pipeline |
| `/api/v1/extract` | POST | NLP free-text field extraction |
| `/api/v1/config` | GET | Dropdown options (sites, tool groups, etc.) |
| `/api/v1/health` | GET | Health check with RAG/LLM status |

## 4. Production Deployment Path

1. **Deploy FastAPI to Azure App Service:**
   ```bash
   az webapp up --name copilot-api --runtime "PYTHON:3.13" --sku B1
   ```

2. **Add Azure AD OAuth:**
   - Register an app in Azure AD
   - Configure the custom connector with OAuth 2.0 authentication
   - Add `AZURE_AD_TENANT_ID` and `AZURE_AD_CLIENT_ID` to App Service config

3. **Update custom connector:**
   - Change the host from `localhost:8000` to your Azure App Service URL
   - Update authentication to OAuth 2.0

4. **Environment variables on Azure:**
   - `HF_TOKEN` — HuggingFace API token for LLM access
   - Set via App Service > Configuration > Application settings

## 5. Modern Enterprise UI Design (Step-by-Step)

This section provides detailed instructions to recreate the modern enterprise UI (matching the React reference) in Power Apps.

### Color Palette

| Use | Hex Code | RGBA |
|-----|----------|------|
| Primary Blue | `#2563eb` | `RGBA(37, 99, 235, 1)` |
| Dark Blue (gradient) | `#4f46e5` | `RGBA(79, 70, 229, 1)` |
| Background | `#f8fafc` | `RGBA(248, 250, 252, 1)` |
| Card Background | `#ffffff` | `RGBA(255, 255, 255, 1)` |
| Border | `#e2e8f0` | `RGBA(226, 232, 240, 1)` |
| Text Primary | `#1e293b` | `RGBA(30, 41, 59, 1)` |
| Text Secondary | `#64748b` | `RGBA(100, 116, 139, 1)` |
| Text Muted | `#94a3b8` | `RGBA(148, 163, 184, 1)` |
| Success Green | `#22c55e` | `RGBA(34, 197, 94, 1)` |
| Priority Critical | `#ef4444` | `RGBA(239, 68, 68, 1)` |
| Priority High | `#f97316` | `RGBA(249, 115, 22, 1)` |
| Priority Medium | `#fbbf24` | `RGBA(251, 191, 36, 1)` |
| Priority Low | `#22c55e` | `RGBA(34, 197, 94, 1)` |

### Step 5.1: Create App and Set Theme

1. **Create new Canvas App** (Tablet format for best layout)
2. **Set App.OnStart:**
   ```
   // Load config from API
   ClearCollect(colConfig, CopilotAPI.GetConfig());

   // Initialize result variable
   Set(varResponse, Blank());
   Set(varLoading, false);
   ```

3. **Set App background:**
   - Fill: `RGBA(248, 250, 252, 1)` (light gray)

### Step 5.2: Screen_Intake - Header

1. **Add Rectangle** (Header background):
   - Position: X=0, Y=0, Width=Parent.Width, Height=70
   - Fill: `RGBA(255, 255, 255, 1)`
   - BorderColor: `RGBA(226, 232, 240, 1)`
   - BorderThickness: 0, 0, 0, 1 (bottom only via shadow workaround)

2. **Add Icon** (Logo):
   - Icon: `Icon.Lightning`
   - Position: X=24, Y=15, Width=40, Height=40
   - Color: `RGBA(255, 255, 255, 1)`
   - Add Rectangle behind it with Fill: `RGBA(37, 99, 235, 1)`, BorderRadius=8

3. **Add Label** (Title):
   - Text: `"Diagnostic AI"`
   - Position: X=80, Y=15
   - Font: Semibold, Size=18
   - Color: `RGBA(30, 41, 59, 1)`

4. **Add Label** (Subtitle):
   - Text: `"MANUFACTURING ENGINEERING PORTAL"`
   - Position: X=80, Y=38
   - Font: Regular, Size=10
   - Color: `RGBA(100, 116, 139, 1)`

### Step 5.3: Screen_Intake - Main Content Card

1. **Add Rectangle** (Card container):
   - Position: X=40, Y=100, Width=Parent.Width-80, Height=600
   - Fill: `RGBA(255, 255, 255, 1)`
   - BorderRadius: 12
   - BorderColor: `RGBA(226, 232, 240, 1)`
   - BorderThickness: 1

2. **Add Label** (Section title):
   - Text: `"Anomaly Intake"`
   - Position: X=70, Y=120
   - Font: Bold, Size=24
   - Color: `RGBA(30, 41, 59, 1)`

3. **Add Label** (Section subtitle):
   - Text: `"Describe the production issue to trigger AI-driven root cause analysis."`
   - Position: X=70, Y=155
   - Font: Regular, Size=14
   - Color: `RGBA(100, 116, 139, 1)`

### Step 5.4: Screen_Intake - Production Context Section

1. **Add Rectangle** (Section header bar):
   - Position: X=70, Y=200, Width=Parent.Width-160, Height=50
   - Fill: `RGBA(248, 250, 252, 1)`
   - BorderRadius: 8, 8, 0, 0 (top only)
   - BorderColor: `RGBA(226, 232, 240, 1)`

2. **Add Label** (Section label):
   - Text: `"PRODUCTION CONTEXT"`
   - Position: X=90, Y=215
   - Font: Semibold, Size=11
   - Color: `RGBA(71, 85, 105, 1)`

3. **Add Dropdowns** (2x2 grid):

   **Dropdown_Site:**
   - Position: X=70, Y=260, Width=350
   - Items: `First(colConfig).sites`
   - BorderRadius: 8

   **Dropdown_ToolGroup:**
   - Position: X=440, Y=260, Width=350
   - Items: `First(colConfig).tool_groups`

   **Dropdown_ProcessStep:**
   - Position: X=70, Y=320, Width=350
   - Items: `First(colConfig).process_steps`

   **Dropdown_Severity:**
   - Position: X=440, Y=320, Width=350
   - Items: `First(colConfig).severity_levels`

4. **Add Labels** above each dropdown:
   - Text: `"Site Location"`, `"Tool Group"`, `"Process Step"`, `"Issue Severity"`
   - Font: Semibold, Size=12
   - Color: `RGBA(71, 85, 105, 1)`

### Step 5.5: Screen_Intake - Issue Description Section

1. **Add Rectangle** (Section header):
   - Position: X=70, Y=380, Width=Parent.Width-160, Height=50
   - Fill: `RGBA(248, 250, 252, 1)`

2. **Add Label**:
   - Text: `"ISSUE NARRATIVE"`
   - Position: X=90, Y=395

3. **Add Badge** (NLP indicator):
   - Add Rectangle: Fill=`RGBA(219, 234, 254, 1)`, BorderRadius=4
   - Add Label inside: Text=`"NLP ENABLED"`, Color=`RGBA(29, 78, 216, 1)`, Size=9, Bold

4. **Add TextInput** (Description):
   - Name: `TextInput_Summary`
   - Position: X=70, Y=440, Width=Parent.Width-160, Height=120
   - Mode: Multiline
   - HintText: `"e.g., Seeing unexpected particle count spikes on tool chamber B after PM cycle..."`
   - BorderRadius: 8
   - BorderColor: `RGBA(226, 232, 240, 1)`

### Step 5.6: Screen_Intake - Submit Button

1. **Add Button**:
   - Name: `Button_Submit`
   - Text: `"Submit Diagnosis"`
   - Position: X=Parent.Width-270, Y=590, Width=200, Height=45
   - Fill: `RGBA(37, 99, 235, 1)`
   - HoverFill: `RGBA(29, 78, 216, 1)`
   - Color: `RGBA(255, 255, 255, 1)`
   - BorderRadius: 8
   - Font: Semibold

2. **OnSelect:**
   ```
   Set(varLoading, true);
   Set(
       varResponse,
       CopilotAPI.Investigate({
           site: Dropdown_Site.Selected.Value,
           tool_group: Dropdown_ToolGroup.Selected.Value,
           process_step: Dropdown_ProcessStep.Selected.Value,
           severity: Dropdown_Severity.Selected.Value,
           anomaly_summary: TextInput_Summary.Text,
           metrics: {
               yield_pct: If(IsBlank(TextInput_Yield.Text), Blank(), Value(TextInput_Yield.Text)),
               affected_lot_count: If(IsBlank(TextInput_Lots.Text), Blank(), Value(TextInput_Lots.Text)),
               time_window_hours: If(IsBlank(TextInput_Hours.Text), Blank(), Value(TextInput_Hours.Text))
           }
       })
   );
   Set(varLoading, false);
   Navigate(Screen_Results);
   ```

### Step 5.7: Screen_Results - Gradient Header

1. **Add Rectangle** (Gradient header simulation):
   - Position: X=40, Y=100, Width=Parent.Width-80, Height=180
   - Fill: `RGBA(37, 99, 235, 1)` (Primary blue - can't do true gradient)
   - BorderRadius: 12, 12, 0, 0

2. **Add Label** (Badge):
   - Text: `"AI DIAGNOSIS"`
   - Position: X=70, Y=120
   - Fill (background rectangle): `RGBA(255, 255, 255, 0.2)`
   - Color: `RGBA(255, 255, 255, 1)`
   - Font: Bold, Size=9

3. **Add Label** (Pattern title):
   - Text: `varResponse.assessment.pattern`
   - Position: X=70, Y=160
   - Color: `RGBA(255, 255, 255, 1)`
   - Font: Bold, Size=28

4. **Add Label** (Diagnostic approach):
   - Text: `varResponse.assessment.diagnostic_approach`
   - Position: X=70, Y=205
   - Color: `RGBA(255, 255, 255, 0.8)`
   - Font: Regular, Size=16

5. **Add Priority Badge** (right side):
   - Rectangle with dynamic Fill based on priority:
     ```
     Switch(
         varResponse.assessment.priority,
         "Critical", RGBA(239, 68, 68, 1),
         "High", RGBA(249, 115, 22, 1),
         "Medium", RGBA(251, 191, 36, 1),
         "Low", RGBA(34, 197, 94, 1),
         RGBA(148, 163, 184, 1)
     )
     ```
   - Label inside: `"Priority: " & varResponse.assessment.priority`

### Step 5.8: Screen_Results - Confidence Section

1. **Add Rectangle** (Section container):
   - Position: X=40, Y=280, Width=Parent.Width-80, Height=100
   - Fill: `RGBA(255, 255, 255, 1)`
   - BorderColor: `RGBA(241, 245, 249, 1)` (bottom border)

2. **Add Label** (Confidence label):
   - Text: `"CONFIDENCE SCORE"`
   - Color: `RGBA(148, 163, 184, 1)`
   - Font: Bold, Size=10

3. **Add Label** (Confidence value):
   - Text:
     ```
     Switch(
         varResponse.assessment.confidence,
         "High", "94%",
         "Medium", "72%",
         "Low", "45%",
         "70%"
     )
     ```
   - Font: Bold, Size=36
   - Color: `RGBA(30, 41, 59, 1)`

4. **Add Rectangle** (Progress bar background):
   - Width=150, Height=12
   - Fill: `RGBA(241, 245, 249, 1)`
   - BorderRadius: 6

5. **Add Rectangle** (Progress bar fill):
   - Width based on confidence (e.g., 141 for 94%)
   - Fill: `RGBA(34, 197, 94, 1)`
   - BorderRadius: 6

### Step 5.9: Screen_Results - Action Plan Gallery

1. **Add Gallery** (Vertical):
   - Name: `Gallery_Actions`
   - Items: `varResponse.next_checks`
   - Position: X=40, Y=400, Width=Parent.Width-80
   - TemplateHeight: 80
   - TemplatePadding: 8

2. **Inside Gallery template:**

   a. **Rectangle** (Step background):
      - Fill: `RGBA(248, 250, 252, 1)`
      - BorderRadius: 8
      - BorderColor: `RGBA(241, 245, 249, 1)`

   b. **Circle** (Step number):
      - Add Circle shape, Fill=`RGBA(37, 99, 235, 1)`, Width=32, Height=32
      - Label inside: `Text(ThisItem.index + 1)`
      - Color: White, Bold

   c. **Label** (Check title):
      - Text: `ThisItem.check`
      - Font: Semibold, Size=14
      - Color: `RGBA(30, 41, 59, 1)`

   d. **Label** (Check reason):
      - Text: `ThisItem.why`
      - Font: Regular, Size=12
      - Color: `RGBA(100, 116, 139, 1)`

### Step 5.10: Screen_Results - Similar Cases Gallery

1. **Add Gallery**:
   - Name: `Gallery_Cases`
   - Items: `varResponse.similar_cases`
   - TemplateHeight: 70

2. **Inside template:**
   - Label: `ThisItem.case_id & " - " & ThisItem.family`
   - Label: `"Resolution: " & ThisItem.resolution`
   - Badge showing similarity score

### Step 5.11: Screen_Results - Back Button

1. **Add Button**:
   - Text: `"< New Diagnosis"`
   - Position: X=40, Y=50
   - Fill: `RGBA(255, 255, 255, 1)`
   - BorderColor: `RGBA(226, 232, 240, 1)`
   - Color: `RGBA(30, 41, 59, 1)`

2. **OnSelect:**
   ```
   Set(varResponse, Blank());
   Navigate(Screen_Intake);
   ```

### Step 5.12: Loading Overlay (Optional)

1. **Add Rectangle** (Overlay):
   - Name: `Overlay_Loading`
   - Position: X=0, Y=0, Width=Parent.Width, Height=Parent.Height
   - Fill: `RGBA(255, 255, 255, 0.9)`
   - Visible: `varLoading`

2. **Add Image** (Spinner):
   - Use a rotating spinner GIF or the built-in Loading indicator
   - Position: Centered

3. **Add Label**:
   - Text: `"Processing Diagnosis..."`
   - Font: Semibold, Size=18

---

## 6. Architecture Overview

```
Power Apps Canvas App
    |
    v
Custom Connector (imports openapi.json)
    |
    v
FastAPI (api/main.py)
    |
    +-- /api/v1/config     -> app/config.py
    +-- /api/v1/investigate -> api/engine_adapter.py -> RAG + LLM pipeline
    +-- /api/v1/extract    -> app/rag_pipeline/llm.py (NLP extraction)
    +-- /api/v1/health     -> status check
    |
    v
Same Python backend as Streamlit app
(rag.py, llm.py, triage.py, placeholder.py)
```

Key design point: The Streamlit app and FastAPI API share the same Python pipeline code. The API layer (`api/engine_adapter.py`) is a thin wrapper that replaces Streamlit-specific constructs (`@st.cache_resource`, `st.warning`) with standard Python equivalents (module singletons, logging).
