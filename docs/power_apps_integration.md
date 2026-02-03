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

## 5. Architecture Overview

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
