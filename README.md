# Laya — Self-hosted System 1 Decision Engine

Dockerized REST API around [Laya](https://github.com/NandhaKishorM/laya)
(`convaiinnovations/laya`), the open-source non-autoregressive decision model
that came out of the TypeSafe **Jev** discussion (Sep 2026).

Laya takes a **state** (text, email, ticket, JSON) plus typed questions and
returns typed answers with calibrated probabilities — in a single forward
pass, no text generation. Runs CPU-only out of the box.

## Endpoints

| Route | Zweck |
|---|---|
| `GET /health` | Status + ob das Modell geladen ist |
| `POST /predict` | Beliebige Fragen im Laya-Schema (`choice` / `score` / `noul`) |
| `POST /triage?message=...` | Preset: Support-Ticket-Triage (Intent, Dringlichkeit, Frust, Churn) |
| `POST /guard?prompt=...` | Preset: Prompt-Guardrails (Jailbreak/Injection-Erkennung) |
| `POST /moderate?post=...` | Preset: Content-Moderation |

## Start

```bash
docker compose up -d --build
```

Der erste Start lädt die Modell-Weights (~1,7 GB) von Hugging Face in den
`hf-cache`-Volume — danach sind Rebuilds ohne Re-Download möglich.

## Beispiel

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

## GPU (optional)

Standard ist CPU. Für GPU den auskommentierten `deploy`-Block in
`docker-compose.yml` aktivieren (braucht `nvidia-container-toolkit`).

## Grenzen

- Nur Englisch, max. 512 Token pro Frage
- Keine Textgenerierung — Arithmetik/Datum in normalem Code lösen
- Modell ist frisch (Apache 2.0, Convai Innovations); Benchmark-Zahlen sind
  Eigenangaben des Autors
