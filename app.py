from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import laya

app = FastAPI(title="Laya - System 1 Decision Engine", version="1.0.0")
agent = None


@app.on_event("startup")
def load_model():
    global agent
    # auto-downloads weights from HF Hub (cached in the hf-cache volume)
    agent = laya.load("convaiinnovations/laya")


class PredictRequest(BaseModel):
    # state: free text or a flat dict (email, ticket, JSON doc ...)
    state: object = Field(..., description="Text or dict representing the state")
    # questions: {"name": {"type": "choice|score|noul", "instructions": str, "criteria": ...}}
    questions: dict = Field(..., description="Typed questions per laya schema")


@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": agent is not None}


@app.post("/predict")
def predict(req: PredictRequest):
    if agent is None:
        raise HTTPException(status_code=503, detail="model not loaded yet")
    try:
        result = agent.predict(req.state, req.questions)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/triage")
def triage(message: str):
    """Preset: support ticket triage (intent, urgency, frustration, churn)."""
    if agent is None:
        raise HTTPException(status_code=503, detail="model not loaded yet")
    return agent.predict({"message": message}, laya.triage_questions())


@app.post("/guard")
def guard(prompt: str):
    """Preset: prompt guardrails (jailbreak, injection, leak detection)."""
    if agent is None:
        raise HTTPException(status_code=503, detail="model not loaded yet")
    return agent.predict({"prompt": prompt}, laya.guard_questions())


@app.post("/moderate")
def moderate(post: str):
    """Preset: content safety & moderation."""
    if agent is None:
        raise HTTPException(status_code=503, detail="model not loaded yet")
    return agent.predict({"post": post}, laya.moderation_questions())
