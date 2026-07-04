# AppScan360.ASoC · Fixer (v3)

A single-file web application that connects **AppScan360** to a locally-running **Ollama** LLM
for privacy-preserving AI vulnerability analysis, compliance mapping, and automated remediation.
Source code and findings never leave your machine.

> **File in use:** `appscan360-fixer-workflow-v3.1.html`  
> `appscan360-fixer-workflow-v3.html` (v3.0) and `appscan360-fixer-workflow.html` (v2.1, dark theme) are kept for rollback only.

---

## Prerequisites — install these once on each machine

| Requirement | Install | Notes |
|---|---|---|
| **Python 3** | Pre-installed on macOS/Linux. Windows: [python.org](https://python.org) | No third-party packages needed — relay uses stdlib only |
| **Ollama** | [ollama.com/download](https://ollama.com/download) | Runs the local LLM; must stay running while using the Fixer |
| **Chrome or Edge** | [google.com/chrome](https://www.google.com/chrome) | Required — Safari lacks the File System Access API needed for patch apply |
| **AppScan360 access** | Contact your AppScan admin | Needs network/VPN access to your AppScan360 host and a valid API key pair |

### Pull an Ollama model (one-time per machine)

```bash
ollama pull mistral          # ~5 GB — recommended starting point
ollama pull gemma4:26b       # Google Gemma 4 26B — good general + code analysis
ollama pull gemma4:31b       # Google Gemma 4 31B — deeper reasoning (GPU recommended)
# OR for best code analysis (GPU recommended):
ollama pull qwen3-coder:30b
```

---

## After Copying to a New Machine

Everything in the Fixer is stored in **browser `localStorage`** — it does **not** travel with the files. When you open the Fixer on a new machine for the first time, reconfigure the following:

| What | Where in the UI | What to enter |
|---|---|---|
| **AppScan360/ASoC URL** | Sidebar → AppScan360 MCP/ASoC MCP → Server URL | Your AppScan360 hostname, e.g. `https://as360aio.appscan.local/mcp` |
| **API Key ID + Secret** | Sidebar → AppScan360 MCP | From AppScan360/ASoC → User Settings → API Management |
| **Ollama model** | Sidebar → Ollama → Refresh Models | Select your downloaded model |
| **GitHub / GitLab / Bitbucket / Azure DevOps token** | Sidebar → Source Control | Personal access token with repo read/write scope |
| **Jira token** | Sidebar → Integrations → Jira | Base URL + email + API token |
| **ServiceNow token** | Sidebar → Integrations → ServiceNow | Instance URL + credentials |
| **SOAR / Slack webhook** | Sidebar → Integrations → SOAR / Slack | Webhook URL |

> **Tip — if you moved the folder:** The relay command in Step 1 below uses `~/Downloads/Fixers/`. If you saved the files elsewhere, update that path accordingly. The Relay URL inside the Fixer (`http://127.0.0.1:8765/mcp`) never changes.

---

## Files in This Folder

| File | Purpose |
|---|---|
| `appscan360-fixer-workflow-v3.1.html` | **The application** — open this in Chrome or Edge |
| `appscan360_mcp_proxy.py` | **Required** — local relay that forwards MCP calls and strips self-signed TLS errors; also handles CORS so the page can talk to `127.0.0.1` |
| `appscan360-issues.json` | Sample issues for offline testing / import |
| `appscan360-fixer-workflow-v3.html` | v3.0 — preserved for rollback |
| `appscan360-fixer-workflow.html` | v2.1 (dark theme) — preserved for rollback |
| `README.md` | This file |

---

## Quick Start

### Step 1 — Start the local MCP relay

The relay is required every time you open the Fixer. Open a terminal and run:

```bash
python3 ~/Downloads/Fixers/appscan360_mcp_proxy.py
```

Expected output:

```
AppScan MCP relay listening on http://127.0.0.1:8765/mcp
```

Keep this terminal open while using the Fixer. To stop it, press **Ctrl+C**.

> **Why is the relay needed?**  
> The Fixer is opened as a `file://` page. Browsers block `file://` pages from calling
> external HTTPS endpoints directly (CORS + self-signed cert rejection). The relay runs
> locally at `http://127.0.0.1:8765` and forwards calls to AppScan360, bypassing both issues.

### Step 2 — Start Ollama with a model

```bash
# Ollama must be running before opening the Fixer
open -a Ollama          # macOS — or it may already be running in the menu bar

# Pull a model if you haven't yet (one-time)
ollama pull mistral                  # ~5 GB — recommended starting point
ollama pull gemma4:26b               # Google Gemma 4 26B — good general + code analysis
ollama pull gemma4:31b               # Google Gemma 4 31B — deeper reasoning (GPU recommended)
# OR for best code analysis (GPU recommended):
ollama pull qwen3-coder:30b
```

Verify Ollama is up:

```bash
curl http://localhost:11434/api/tags
# Expected: JSON with a "models" array
```

### Step 3 — Open the Fixer

```bash
open ~/Downloads/Fixers/appscan360-fixer-workflow-v3.1.html
```

Or double-click the file in Finder. Use **Chrome** or **Edge** — Safari has limited File System
Access API support (needed for local patch apply).

### Step 4 — Connect MCP

In the left sidebar, expand the **AppScan360 MCP** card and fill in:

| Field | Value |
|---|---|
| **Server URL** | `https://as360aio.appscan.local/mcp` (your AppScan endpoint) |
| **Relay URL** | `http://127.0.0.1:8765/mcp` *(pre-filled — do not change)* |
| **API Key ID** | From AppScan360 → User Settings → API Management |
| **API Key Secret** | The secret paired with the Key ID |

Click **Connect**. The status dot turns green: **MCP: connected**.

### Step 5 — Connect Ollama

In the **Ollama** card:

1. Confirm Base URL is `http://localhost:11434`.
2. Click **Refresh Models** and select your downloaded model.
3. The status dot turns green: **Ollama: connected**.

You are ready to use all features.

---

## Navigation

The tab bar is organized into four groups:

| Group | Tabs |
|---|---|
| *(standalone)* | **Chat & Analysis** |
| **Configuration** | Repository · Remediation Workspace |
| **Statistics & Details** | Asset Groups · Applications · Scans · Issues · **Compliance** |
| **Tools** | Auto-Fix Workflow · Mapping History · Integration Code · Event Log |

---

## Features

### Chat & Analysis

Ask natural-language questions about your scan data. The AI uses MCP tool calls to pull live
data and answers in context with your findings.

Examples:
- *"Summarize all open Critical issues"*
- *"What are the top 5 CWEs in my last scan?"*
- *"Generate a risk report for application Knox_AltoroJ"*

### Applications / Asset Groups / Scans / Issues

Browse AppScan360 data. Issues support scope-filtered loading:

1. Go to **Issues** → select Asset Group → Application → Scan (narrowest scope = fastest load).
2. Click **Load Issues**.
3. Filter by severity or text search, or **Export JSON**.

### Compliance

Maps every loaded finding to violated sections of your chosen compliance standards.

#### Scope selector

Before clicking **Analyze Compliance**, choose which issues to analyze:

| Mode | Behavior |
|---|---|
| **Current Issues (Issues tab)** | Analyzes whatever is currently loaded in the Issues tab |
| **By Application** | Fetches issues for the selected application on demand via MCP |
| **By Asset Group** | Fetches issues for all applications in the selected asset group (top 8 by issue count, in parallel) |

> Applications must be loaded first (visit the Applications or Asset Groups tab) before
> the By Application / By Asset Group dropdowns are populated.

#### Compliance targets

Select one or more standards from the **AppScan Compliance Targets** list (Cmd/Ctrl-click
for multi-select). Covered standards include:

- OWASP Top 10 (2017 / 2021 / 2025), OWASP API Security, OWASP ASVS
- CWE Top 25, PCI DSS v4, NIST SP 800-53, ISO 27001/27002, WASC
- Regulatory: GDPR, CCPA, PCI DSS, SOX, FedRAMP, FISMA, HIPAA, DORA, NIS2, PoPIA, and more

Click **Analyze Compliance**. Results appear in three sections:

- **Violations by Standard & Section** — each standard with its violated controls and finding counts
- **Violations by Application** — which standards/sections each application breaches
- **Violations by Finding** — every violating issue with its exact `standard: section` mapping

A compact **Compliance Violations** block also appears inline on the **Issues** and
**Applications** tabs, and inside the issue detail modal, when targets are selected.

#### Export Report as HTML

After analysis, click **⬇ Export Report as HTML** below the results. A self-contained HTML
file is downloaded (`compliance-report-YYYY-MM-DDTHH-MM-SS.html`) with:

- Report header: generated timestamp, scope, and selected standards
- All three result sections with full tables and severity badges
- A **Print / Save as PDF** button for sharing as PDF

### Repository

Connect a local source folder and build a file index for remediation mapping.

1. Click **Choose Directory** → select your project root.
2. Click **Connect Repository** → **Start Index**.
3. Wait for the file/symbol count to appear.

### Remediation Workspace

End-to-end remediation loop:

1. In Issues tab → click **Map to code** on a finding.
2. In Remediation Workspace → **Load Issue Detail**.
3. **Suggest Candidates** → select the best-matched file → **Set Primary**.
4. **Generate Plan** → **Generate Patch Draft**.
5. Review **Vulnerable Code**, **Patched Code**, and **Line Diff** tabs.
6. **Apply Patch to File** → writes directly to the local file.
7. **Share Plan/Patch to Issue Comment** → posts to the AppScan360 issue.
8. **Save Mapping** → stores an audit record.

### Auto-Fix Workflow *(Tools group)*

Automated pipeline across many issues at once:

> **Pull from AppScan → Triage → Validate → Map to source → Fix Plan → In-Context → In-Code → Human approval → Branch + PR/MR**

Supports GitHub, GitLab, Bitbucket, Azure DevOps, and Local write.

The **MCP Chain** fires on approval:
commit + PR → flip AppScan status → Jira ticket → ServiceNow incident → SOAR webhook → Slack.

Configure providers in the sidebar **Integrations** cards (persisted to `localStorage`).

---

## Troubleshooting

### MCP / Relay

| Symptom | Likely cause | Fix |
|---|---|---|
| "Ensure the local relay is running" toast | Relay not started | Run `python3 ~/Downloads/Fixers/appscan360_mcp_proxy.py` |
| Relay starts then exits immediately | Port 8765 already in use | `lsof -i :8765` → `kill <PID>` → restart relay |
| 502 Bad Gateway | Relay running but AppScan unreachable | Check AppScan360 service / VPN / hosts file |
| 401 Unauthorized | Wrong API Key ID or Secret | Regenerate in AppScan360 → User Settings → API Management |
| MCP connects but no data loads | Key lacks permissions | Ensure key has Read access to Issues, Applications, Scans |
| CORS error in browser console | Old relay without Private Network header | Make sure you're using the `appscan360_mcp_proxy.py` from this folder (updated July 2026) |

### Ollama

| Symptom | Likely cause | Fix |
|---|---|---|
| "Cannot reach Ollama" | Ollama not running | `open -a Ollama` (macOS) / `sudo systemctl start ollama` (Linux) |
| Model dropdown empty | No models pulled | `ollama pull mistral` then **Refresh Models** |
| Very slow responses | Model too large for available RAM | Switch to `mistral` or `orca-mini` |

### Compliance

| Symptom | Fix |
|---|---|
| Application / Asset Group dropdowns empty | Visit the Applications or Asset Groups tab first to load `state.applications` |
| "No issues loaded" after Analyze | For By Application/Asset Group: check Event Log for the MCP fetch error; confirm relay is running |
| Export button not visible | Compliance analysis must complete successfully first |

### General

| Symptom | Fix |
|---|---|
| Page blank after open | Hard-reload: Cmd+Shift+R (macOS) / Ctrl+Shift+R (Windows) |
| "Choose Directory" button missing | Use Chrome or Edge — Safari has limited File System Access API support |
| Jira / ServiceNow calls fail | Set the **API Proxy** field in the Integrations sidebar (cross-origin calls from `file://` are blocked by those services) |

### Diagnostics checklist

When reporting a problem, collect:
1. Browser type and version
2. Ollama version (`ollama --version`) and model in use
3. AppScan360 version
4. Contents of the **Event Log** tab (copy relevant lines)
5. Browser console errors (F12 → Console)


---

*Last updated: 2026-07-01*
