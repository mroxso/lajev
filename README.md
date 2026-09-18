# Laya — Self-hosted System 1 Decision Engine

Dockerized REST API around [Laya](https://github.com/NandhaKishorM/laya)
(`convaiinnovations/laya`), the open-source non-autoregressive decision model
that came out of the TypeSafe **Jev** discussion (Sep 2026).

Laya takes a **state** (text, email, ticket, JSON) plus typed questions and
returns typed answers with calibrated probabilities — in a single forward
pass, no text generation. Runs CPU-only out of the box.

## Endpoints

| Route | Purpose |
|---|---|
| `GET /health` | Status + whether the model is loaded |
| `POST /predict` | Arbitrary questions in the Laya schema (`choice` / `score` / `noul`) |
| `POST /triage?message=...` | Preset: support ticket triage (intent, urgency, frustration, churn) |
| `POST /guard?prompt=...` | Preset: prompt guardrails (jailbreak/injection detection) |
| `POST /moderate?post=...` | Preset: content moderation |
| `POST /v1/systemone` | TypeSafe-API-compatible endpoint (`state` + `model` + `questions` → `answers` + `usage`). Any `Authorization` header, or none, is accepted — this deployment has no API keys to check. |

## Getting started

```bash
docker compose up -d --build
```

The first startup downloads the model weights (~1.7 GB) from Hugging Face
into the `hf-cache` volume — after that, rebuilds don't re-download.

## Example

```bash
curl -s localhost:8100/predict -H 'Content-Type: application/json' -d '{
  "state": {
    "from": "user@acme.com",
    "subject": "Duplicate charge on invoice #4411",
    "body": "We were billed twice for March. Refund or we cancel."
  },
  "questions": {
    "department": {
      "type": "choice",
      "instructions": "Which department should handle this email?",
      "criteria": {
        "billing":   "invoices, payments, refunds",
        "technical": "bugs, outages, system errors",
        "sales":     "pricing, new contracts",
        "other":     "everything else"
      }
    },
    "urgency": {
      "type": "score",
      "instructions": "How urgent is this request?",
      "criteria": ["not urgent", "soon", "critical deadline or blocking issue"]
    },
    "churn_risk": {
      "type": "noul",
      "instructions": "Does the user threaten to cancel or leave?"
    }
  }
}'
```

TypeSafe-compatible call to `/v1/systemone` (same shape as `api.typesafe.ai/v1/systemone`; `model` and `Authorization` are accepted but ignored):

```bash
curl -s localhost:8100/v1/systemone \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer sk-anything' \
  -d '{
  "model": "jev-latest",
  "state": "We were billed twice for March. Refund or we cancel.",
  "questions": {
    "urgency": {
      "type": "score",
      "instructions": "How urgent is this request?",
      "criteria": ["not urgent", "soon", "critical deadline or blocking issue"]
    },
    "churn_risk": {
      "type": "noul",
      "instructions": "Does the user threaten to cancel or leave?"
    }
  }
}'
```

## GPU (optional)

CPU-only by default. To use a GPU, uncomment the `deploy` block in
`docker-compose.yml` (requires `nvidia-container-toolkit`).

## Limitations

- English only, max 512 tokens per question
- No text generation — solve arithmetic/dates in regular code
- The model is brand new (Apache 2.0, Convai Innovations); benchmark numbers
  are the author's own claims
