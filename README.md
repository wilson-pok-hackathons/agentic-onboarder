# Relay — agentic onboarding MVP

A server-rendered Django operations console for configuring and observing resumable onboarding agents.

## What works

- Two seeded organizations using one generic workflow engine
- Organization workflow and integration overview
- Structured onboarding intake
- Persistent runs, steps, tool results, and activity events
- Automatic simulated execution with idempotency keys
- Safe pause for missing information and resume without replaying completed work
- Completion verification report
- Explicit integration boundaries for Google ADK/Gemini and Firestore

## Run locally

```powershell
python manage.py migrate
python manage.py runserver
```

Open `http://127.0.0.1:8000`. Start a Northstar Models onboarding and leave email blank to exercise pause/resume.

## Google integration configuration

Local simulation is the default and requires no cloud credentials. Production wiring is isolated under `core/integrations/`.

```text
GOOGLE_CLOUD_PROJECT=your-project
WORKFLOW_STATE_BACKEND=firestore
```

Install `google-cloud-firestore` before selecting the Firestore backend. The ADK planner intentionally raises `NotImplementedError` until the project has selected its model, authentication strategy, and deployment credentials; it does not silently pretend a model call succeeded.
