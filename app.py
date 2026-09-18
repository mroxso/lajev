from typing import Annotated, Any, Dict, List, Literal, Optional, Union

from fastapi import FastAPI, Header, HTTPException
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


# ---------------------------------------------------------------------------
# TypeSafe-compatible endpoint
#
# Mirrors the request/response contract of POST https://api.typesafe.ai/v1/systemone
# so that clients written against the TypeSafe API can point at this
# self-hosted laya deployment unchanged. No API key is required: any
# Authorization header, or none at all, is accepted and ignored.
# ---------------------------------------------------------------------------

StateType = Union[str, Dict[str, Any], List[Any]]
InstructionsType = Union[str, Dict[str, Any], List[Any]]


class NoulCriteria(BaseModel):
    true: Optional[str] = None
    false: Optional[str] = None


class NoulQuestion(BaseModel):
    type: Literal["noul"]
    instructions: InstructionsType
    criteria: Optional[NoulCriteria] = None


class ChoiceQuestion(BaseModel):
    type: Literal["choice"]
    instructions: InstructionsType
    criteria: Dict[str, Optional[str]]


class ScoreQuestion(BaseModel):
    type: Literal["score"]
    instructions: InstructionsType
    criteria: List[str] = Field(..., min_length=2)


Question = Annotated[Union[NoulQuestion, ChoiceQuestion, ScoreQuestion], Field(discriminator="type")]


class SystemOneRequest(BaseModel):
    state: StateType = Field(..., description="Text, or structured data to evaluate")
    model: str = Field(..., description="Requested model id, e.g. 'jev-latest'. Ignored: this deployment always answers with its own local laya model.")
    questions: Dict[str, Question]


class Usage(BaseModel):
    input_tokens: int
    output_tokens: int


class NoulAnswer(BaseModel):
    type: Literal["noul"]
    noul: float = Field(..., description="0 (no) to 1 (yes)")


class ChoiceAnswer(BaseModel):
    type: Literal["choice"]
    choice: str
    probabilities: Dict[str, float]
    confidence: float


class ScoreAnswer(BaseModel):
    type: Literal["score"]
    score: float
    legend: Dict[str, str]
    probabilities: Dict[str, float]
    confidence: float


Answer = Annotated[Union[NoulAnswer, ChoiceAnswer, ScoreAnswer], Field(discriminator="type")]


class SystemOneResponse(BaseModel):
    model: str
    answers: Dict[str, Answer]
    usage: Usage


@app.post("/v1/systemone", response_model=SystemOneResponse)
def systemone(req: SystemOneRequest, authorization: Optional[str] = Header(default=None)):
    """TypeSafe-compatible evaluation endpoint (parity with POST /v1/systemone).

    Authentication is not enforced here: any bearer token, or no
    Authorization header at all, is accepted since this deployment has no
    API keys of its own to check.
    """
    if agent is None:
        raise HTTPException(status_code=503, detail="model not loaded yet")
    questions = {qid: q.model_dump(exclude_none=True) for qid, q in req.questions.items()}
    try:
        return agent.predict(req.state, questions)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))
