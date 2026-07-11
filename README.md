# AppScan360.ASoC · Fixer (v3)

A single-file web application that connects **AppScan360/AppScan on Cloud** to an **LLM provider**
— local Ollama, OpenAI, Google Gemini, Anthropic Claude, or GitHub Copilot —
for AI-assisted vulnerability analysis, compliance mapping, and automated remediation.
Source code and findings never leave your machine (local Ollama) or only leave via your own API key (commercial providers).

> **File in use:** `appscan360-fixer-workflow-v3.4.html`  
> `appscan360-fixer-workflow-v3.3.html` (v3.3) is kept for rollback. `appscan360-fixer-workflow-v3.1.html` (v3.1) and `appscan360-fixer-workflow-v3.html` (v3.0) are legacy only.

---

## Prerequisites — install these once on each machine

| Requirement | Install | Notes |
|---|---|---|
| **Python 3** | Pre-installed on macOS/Linux. Windows: [python.org](https://python.org) | No third-party packages needed — relay uses stdlib only |
| **Ollama** *(optional)* | [ollama.com/download](https://ollama.com/download) | Only required for local LLM mode; skip if using OpenAI / Gemini / Claude / Copilot |
| **Chrome or Edge** | [google.com/chrome](https://www.google.com/chrome) | Required — Safari lacks the File System Access API needed for patch apply |
| **AppScan360 access** | Contact your AppScan admin | Needs network/VPN access to your AppScan360 host and a valid API key pair |

### Option A — Local LLM (Ollama, free, private)

```bash
# Pull a model — one-time per machine
ollama pull mistral          # ~5 GB — fastest, good for triage on CPU
ollama pull gemma4:12b       # 7.6 GB — strong all-rounder
ollama pull gemma4:26b       # 17 GB — best quality on 36 GB+ RAM
ollama pull qwen3-coder:30b  # 18 GB — best for code analysis
```

### Option B — Commercial LLM (OpenAI / Gemini / Claude / Copilot)

No installation needed. You just need an API key:

| Provider | Get key at | Notes |
|---|---|---|
| **OpenAI** | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) | gpt-4o recommended |
| **Google Gemini** | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) | gemini-2.0-flash is free-tier |
| **Anthropic Claude** | [console.anthropic.com](https://console.anthropic.com) | claude-sonnet-4-5 recommended |
| **GitHub Copilot** | GitHub → Settings → Developer settings → Personal access tokens | Requires active Copilot subscription |

---

## After Copying to a New Machine

Everything in the Fixer is stored in **browser `localStorage`** — it does **not** travel with the files. When you open the Fixer on a new machine for the first time, reconfigure the following:

| What | Where in the UI | What to enter |
|---|---|---|
| **AppScan360/ASoC URL** | Sidebar → AppScan360 MCP → Server URL | Your AppScan360 hostname, e.g. `https://as360aio.appscan.local/mcp` |
| **API Key ID + Secret** | Sidebar → AppScan360 MCP | From AppScan360/ASoC → User Settings → API Management |
| **LLM Provider** | Sidebar → LLM Provider → Provider | Select Ollama, OpenAI, Gemini, Claude, or Copilot |
| **LLM API Key** | Sidebar → LLM Provider → API Key | Commercial providers only — paste your provider API key |
| **LLM Model** | Sidebar → LLM Provider → Model | Select (Ollama) or type (commercial) the model name |
| **GitHub / GitLab / Bitbucket / Azure DevOps token** | Sidebar → Source Control | Personal access token with repo read/write scope |
| **Jira token** | Sidebar → Integrations → Jira | Base URL + email + API token |
| **ServiceNow token** | Sidebar → Integrations → ServiceNow | Instance URL + credentials |
| **SOAR / Slack webhook** | Sidebar → Integrations → SOAR / Slack | Webhook URL |

> **Tip — if you moved the folder:** The relay command in Step 1 below uses `~/Downloads/Fixers/`. If you saved the files elsewhere, update that path accordingly. The Relay URL inside the Fixer (`http://127.0.0.1:8765/mcp`) never changes.

---

## Files in This Folder

| File | Purpose |
|---|---|
| `appscan360-fixer-workflow-v3.4.html` | **The application (latest)** — v3.4 multi-provider LLM |
| `appscan360-fixer-workflow-v3.3.html` | v3.3 — preserved for rollback |
| `appscan360_mcp_proxy.py` | **Required** — local relay that forwards MCP calls and strips self-signed TLS errors; also handles CORS so the page can talk to `127.0.0.1` |
| `appscan360-issues.json` | Sample issues for offline testing / import |
| `appscan360-fixer-workflow-v3.1.html` | v3.1 — preserved for rollback |
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
  MCP endpoint  : http://127.0.0.1:8765/mcp
  Ollama relay  : http://127.0.0.1:8765/ollama/chat
  LLM relay     : http://127.0.0.1:8765/llm/chat  (OpenAI / Gemini / Claude / Copilot)
```

Keep this terminal open while using the Fixer. To stop it, press **Ctrl+C**.

> **Why is the relay needed?**  
> The Fixer is opened as a `file://` page. Browsers block `file://` pages from calling
> external HTTPS endpoints directly (CORS + self-signed cert rejection). The relay runs
> locally at `http://127.0.0.1:8765` and forwards calls to AppScan360, bypassing both issues.

### Step 2 — Choose your LLM provider

**Option A — Ollama (local, free)**
```bash
open -a Ollama   # macOS — or it may already be running in the menu bar
curl http://localhost:11434/api/tags   # verify it's up
```

**Option B — Commercial provider (OpenAI / Gemini / Claude / Copilot)**  
No local setup needed — just have your API key ready (configure in sidebar Step 5).

### Step 3 — Open the Fixer

```bash
open ~/Downloads/Fixers/appscan360-fixer-workflow-v3.4.html
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

### Step 5 — Connect LLM Provider

In the **LLM Provider** card (click to expand):

**Ollama:**
1. Confirm Base URL is `http://localhost:11434`.
2. Select a model from the dropdown (pre-populated with common models).
3. Click **Connect** — the status dot turns green: **LLM: Ollama · mistral**.

**Commercial provider (OpenAI / Gemini / Claude / Copilot):**
1. Select the provider from the dropdown.
2. Paste your API key.
3. Type or select the model name (e.g. `gpt-4o`, `gemini-2.0-flash`, `claude-sonnet-4-5`).
4. Click **Connect** — the status dot turns green: **LLM: Claude · claude-sonnet-4-5**.

You are ready to use all features.

---

## Navigation

The tab bar is organized into four groups:

| Group | Tabs |
|---|---|
| *(standalone)* | **Chat & Analysis** |
| **Configuration** | Repository · Remediation Workspace |
| **Statistics & Details** | Asset Groups · Applications · Scans · Issues · **Compliance** |
| **Tools** | Auto-Fix Workflow · **Triage & Fix** · Mapping History · Integration Code · Event Log |

---

## Features

### Chat & Analysis

Ask natural-language questions about your scan data. The AI uses MCP tool calls to pull live
data and answers in context with your findings.

Examples:
- *"Summarize all open Critical issues"*
- *"What are the top 5 CWEs in my last scan?"*
- *"Generate a risk report for application Knox_AltoroJ"*

### LLM Provider *(v3.4)*

Choose your AI backend from the **LLM Provider** sidebar card:

| Provider | Type | Model examples | Max output tokens |
|---|---|---|---|
| **Ollama** | Local — private | mistral, gemma4:12b/26b, qwen3-coder:30b | model-dependent |
| **OpenAI** | Commercial | gpt-4o, gpt-4o-mini, o3-mini | 16,384 |
| **Google Gemini** | Commercial | gemini-2.0-flash, gemini-1.5-pro | 8,192 |
| **Anthropic Claude** | Commercial | claude-sonnet-4-5, claude-opus-4 | 64,000 |
| **GitHub Copilot** | Commercial | gpt-4o, claude-sonnet-4-5 | 4,096 |

All commercial providers route through the local relay (`/llm/chat`) — the API key never touches the AppScan360 server. Output token limits are enforced automatically.

**Ollama context window recommendations** (36 GB unified memory):

| Model | Size | Recommended `num_ctx` |
|---|---|---|
| `gemma4:12b` | 7.6 GB | 16,384 |
| `gemma4:e4b` | 9.6 GB | 16,384 |
| `gemma4:26b` | 17 GB | 8,192 |
| `qwen3-coder:30b` | 18 GB | 8,192 |
| `llama4:scout` | 67 GB ⚠️ | 8,192 (exceeds 36 GB RAM — slow) |

### Asset Groups

Displays all asset groups from AppScan360. In v3.3, the tab performs a **direct `get_asset_groups` MCP call** to retrieve the authoritative group list — groups with no locally-visible applications (e.g. empty groups or access-scoped groups) are now shown. App-derived issue counts are merged in where available.

### Applications / Scans / Issues

Browse AppScan360 data. Issues support scope-filtered loading:

1. Go to **Issues** → select Asset Group → Application → Scan (narrowest scope = fastest load).
2. Click **Load Issues**.
3. Filter by severity or text search, or **Export JSON**.
4. Use the **checkboxes** to select issues for Triage & Fix (checking does not open the detail modal).
5. Click a row (not the checkbox) to open the issue detail modal and **Ask AI for remediation**.

### Triage & Fix *(v3.3 — Tools group)*

Batch AI triage and remediation planning across selected issues using any configured LLM.

**Workflow:**

1. In the **Issues** tab, tick the checkboxes next to the issues you want to analyze.
2. Click **▶ Triage & Fix** in the toolbar (or use **Select all**).
3. Switch to the **Triage & Fix** tab to watch results stream in real time.
4. Each issue runs two sequential LLM calls:
   - **Call 1 — Triage:** Returns a JSON object with `priority`, `exploitability`, `businessImpact`, `effort`, and `triageSummary`.
   - **Call 2 — Fix:** Returns a structured markdown remediation plan (`## Root Cause`, `## Fix`, `## Verification`).
5. Click **▶ Details** on any row to expand the full triage summary and fix plan.
6. Use **⬇ Export HTML** to download all results as a self-contained report.
7. Use **→ Send to Auto-Fix** to push selected issues into the Auto-Fix Workflow pipeline.

**Model recommendations for Triage & Fix:**

| Model | Notes |
|---|---|
| `gemma4:26b` (Ollama) | Good balance — handles thinking-model JSON correctly |
| `qwen3-coder:30b` (Ollama) | Best for code-specific fix plans |
| `mistral` (Ollama) | Fastest — good for triage on CPU-only machines |
| `claude-sonnet-4-5` | Excellent reasoning quality (commercial) |
| `gpt-4o` | Reliable JSON output for structured triage (commercial) |

> **Tip:** The Triage & Fix tab caps context window per call (16k for triage, 32k for fix) regardless of the sidebar `num_ctx` setting, to prevent OOM crashes during sequential analysis.

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

### LLM Provider *(v3.4)*

| Symptom | Likely cause | Fix |
|---|---|---|
| LLM dot stays orange | Not clicked Connect yet | Click the **Connect** button in the LLM Provider card |
| "Enter your API key" error | API key not entered | Expand LLM Provider card → paste your key → Connect |
| "Provider error (400): max_tokens" | Old stored value too high | Switch provider and back — the field auto-resets to the safe cap |
| "Provider error (401)" | Invalid API key | Check/regenerate your key at the provider's dashboard |
| "Provider error (400): model not found" | Wrong model name | Check exact model ID (e.g. `claude-sonnet-4-5` not `claude-sonnet`) |
| Responses very slow / timeout | Ollama model too large for RAM | Use a smaller model (`gemma4:12b` or `mistral`) |
| Commercial provider working in Connect test but fails in Chat | Context too large | Reduce Max Tokens in the sidebar |

### Ollama

| Symptom | Likely cause | Fix |
|---|---|---|
| "Cannot reach Ollama" | Ollama not running | `open -a Ollama` (macOS) / `sudo systemctl start ollama` (Linux) |
| Model dropdown shows defaults only | Ollama not running or relay not started | Start relay + Ollama, then click **Connect** |
| Very slow responses | Model too large for available RAM | Switch to `gemma4:12b` or `mistral` |
| "No valid JSON in model response" | Thinking model (gemma4) put JSON inside `<think>` block | v3.4 strips `<think>` blocks automatically |
| "to/to/to/to/…" repetition in triage | Token loop | v3.4 adds `repeat_penalty: 1.15` automatically |

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

*Last updated: 2026-07-12*
