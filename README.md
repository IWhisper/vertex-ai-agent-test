# Multi-Agent ADK → Vertex AI Deployment Guide

This project is a Multi-Agent system built with **Google ADK (Agent Development Kit)** and deployed to **Vertex AI Agent Engine**. This document covers the key steps to deploy an ADK project to the cloud.

## Project Structure

```
vertex-ai-agent/
├── orchestrator_agent/
│   ├── agent.py          # Root Agent: defines OrchestratorApp (AdkApp subclass)
│   └── instructions.py   # Orchestrator routing instructions
├── sub_agents/
│   ├── rss_agent/
│   │   ├── agent.py        # RSS summarizer Agent
│   │   ├── instructions.py # RSS Agent instructions (includes default URL)
│   │   └── tools.py        # fetch_rss_feed tool (with default URL parameter)
│   └── market_agent/
│       ├── agent.py        # Market analyst Agent
│       ├── instructions.py # Market instructions (with dynamic date injection)
│       └── tools.py        # fetch_major_indices / fetch_top_tech_stocks
├── deploy_from_source.py   # Deployment script
├── test_local.py           # Local testing (InMemoryRunner)
├── test_deployed.py        # Cloud testing (stream / sync modes)
└── requirements.txt
```

---

## Key Steps: From ADK Project to Vertex AI

### 1. Define an AdkApp Entry Point

Vertex AI only recognizes `AdkApp` instances. Wrap your root agent with it:

```python
from vertexai.agent_engines import AdkApp
from google.adk.agents import Agent

root_agent = Agent(name="my_agent", ...)
app = AdkApp(agent=root_agent)
```

**AdkApp only exposes streaming interfaces by default** (`stream_query` / `async_stream_query`). There is no blocking `query()` method. If you need blocking, subclass `AdkApp` and implement it yourself (see `orchestrator_agent/agent.py`).

#### AdkApp Built-in Methods

All of these methods exist on every `AdkApp` instance. **They still need to be declared in `class_methods` when using `source_packages` deployment** — Vertex AI won't expose them unless you explicitly register them.

| Method | Type | Description |
|---|---|---|
| `stream_query` | Primary interface | Streaming query — yields response chunks in real-time |
| `async_stream_query` | Primary interface | Async version of stream_query |
| `create_session` | Session mgmt | Create a new conversation session for a user |
| `async_create_session` | Session mgmt | Async version |
| `get_session` | Session mgmt | Retrieve an existing session by ID |
| `async_get_session` | Session mgmt | Async version |
| `list_sessions` | Session mgmt | List all sessions for a given user |
| `async_list_sessions` | Session mgmt | Async version |
| `delete_session` | Session mgmt | Delete a session |
| `async_delete_session` | Session mgmt | Async version |
| `async_add_session_to_memory` | Memory | Persist a session into long-term memory |
| `async_search_memory` | Memory | Search long-term memory |

> **`query` is custom** — not built into `AdkApp`. See `orchestrator_agent/agent.py` for how we implemented it as a blocking wrapper around `stream_query`.

---

### 2. Environment Setup

Copy `.env.example` to `.env` and fill in your values:

```
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=your-location   # e.g. europe-west1
```

Also authenticate locally with:

```bash
gcloud auth application-default login
```

#### Alternative: Service Account JSON Key (if gcloud is not available)

> **⚠️ Disabled by default** — GCP organizations typically enforce a policy (`constraints/iam.disableServiceAccountKeyCreation`) that blocks JSON key exports. This is a security best practice: JSON keys are long-lived credentials that can be leaked and are hard to rotate automatically. Google recommends using short-lived tokens from `gcloud` or Workload Identity instead.

If your org allows it, or you need this for a CI/CD environment without gcloud, you can create and use a JSON key:

```bash
# 1. Create a service account with the required roles, then export a key:
gcloud iam service-accounts keys create key.json \
  --iam-account=YOUR_SA@YOUR_PROJECT.iam.gserviceaccount.com
```

Then **export** it in your shell (not in `.env` — see note below):

```bash
export GOOGLE_APPLICATION_CREDENTIALS=/absolute/path/to/key.json
```

> **Why `export` and not `.env`?** `GOOGLE_APPLICATION_CREDENTIALS` is read by the underlying `google-auth` library at module import time. Using `export` makes it available to all scripts automatically without any code changes.
> If you put it in `.env` instead, `test_local.py` (which uses `dotenv_values()`) would need an extra line to set it manually — `export` is simpler and more universal.

> **⚠️ Never commit `key.json` to git.** It's already covered by `*.json` in `.gitignore`.

**To override the org policy** (requires `roles/orgpolicy.policyAdmin`):

```bash
gcloud resource-manager org-policies disable-enforce \
  constraints/iam.disableServiceAccountKeyCreation \
  --project=YOUR_PROJECT_ID
```

Or via GCP Console: IAM & Admin → Organization Policies → search `disableServiceAccountKeyCreation` → Edit → set to **Not enforced** for your project.

> **Note:** `.env` is listed in both `.gitignore` and `.gcloudignore` — it will never be committed or uploaded to the cloud.

---

### 3. Local Testing with `InMemoryRunner`

`AdkApp` has no `.query()` method locally. Use `google.adk.runners.InMemoryRunner` instead.

**Critical:** the environment variables must be set **before** any `google.adk` / `google.genai` imports, because ADK reads them at module load time to decide which LLM backend to use:

```python
from dotenv import dotenv_values
import os

# Load and set BEFORE any google imports
_env = dotenv_values(".env")
os.environ["GOOGLE_CLOUD_PROJECT"] = _env["GOOGLE_CLOUD_PROJECT"]
os.environ["GOOGLE_CLOUD_LOCATION"] = _env["GOOGLE_CLOUD_LOCATION"]
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "true"

from google.adk.runners import InMemoryRunner  # import AFTER env vars are set
runner = InMemoryRunner(agent=root_agent, app_name="my_app")
```

---

### 4. Deployment: `source_packages` Mode Requires `class_methods`

When deploying with `source_packages` (recommended — no object serialization needed), the SDK **requires** you to explicitly declare which methods to expose:

```python
client = vertexai.Client(project=PROJECT_ID, location=LOCATION)
remote = client.agent_engines.create(config={
    "display_name": "Multi-Agent",
    "description": "An orchestrated multi-agent system",
    "source_packages": ["."],
    "entrypoint_module": "orchestrator_agent.agent",
    "entrypoint_object": "app",
    "requirements_file": "requirements.txt",
    "class_methods": [
        {
            "name": "stream_query",
            "api_mode": "stream",   # Must be lowercase
            "parameters": {
                "properties": {
                    "user_id": {"type": "string"},
                    "message": {"type": "string"},
                },
                "required": ["user_id", "message"],
                "type": "object"
            }
        },
        # Multiple methods can be registered simultaneously.
        # Supported api_mode values: "", "stream", "async", "async_stream"
        {
            "name": "create_session",
            "api_mode": "",
            "parameters": {
                "properties": {
                    "user_id": {"type": "string", "description": "The user ID."},
                },
                "required": ["user_id"],
                "type": "object"
            }
        },
    ]
})
```

> **⚠️ Gotcha:** `api_mode` must be lowercase (`"stream"`, not `"STREAM"`). Using uppercase causes the method registration to silently fail — deployment succeeds but the method is unavailable.

---

### 3. Parsing `stream_query` Output in Cloud Tests

Each chunk from `stream_query` is a `dict` with the following structure:

```python
for chunk in remote_agent.stream_query(user_id="u1", message="hello"):
    author = chunk.get("author")                                       # Which agent produced this
    transfer = chunk.get("actions", {}).get("transfer_to_agent")       # Agent handoff, if any
    parts = chunk.get("content", {}).get("parts", [])
    for part in parts:
        if "text" in part:                # Text output
            print(part["text"])
        elif "function_call" in part:     # Tool invocation
            ...
        elif "function_response" in part: # Tool result
            ...
```

---

## Run Locally

```bash
python test_local.py
```

## Deploy

```bash
python deploy_from_source.py
# Copy the printed Resource Name and update it in test_deployed.py
```

## Test in Cloud

```bash
python test_deployed.py --mode stream  # Shows routing chain + final output
python test_deployed.py --mode sync    # Shows final output only
```

---

## Required IAM Roles

Granted at the **GCP project level** in IAM & Admin → IAM:

| Scenario | Role |
|---|---|
| Local dev / cloud test only | `Vertex AI User` (`roles/aiplatform.user`) |
| Deploy (`deploy_from_source.py`) | + `Vertex AI Reasoning Engine Admin` + `Storage Object Admin` |
| One role for everything | `Vertex AI Administrator` (`roles/aiplatform.admin`) |
