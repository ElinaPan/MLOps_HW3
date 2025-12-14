import os
import pickle
from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

MODEL_VERSION = os.getenv("MODEL_VERSION", "v1.0.0")

MODEL_PATH = Path(__file__).parent / "model.pkl"
with open(MODEL_PATH, "rb") as f:
    model = pickle.load(f)

class Input(BaseModel):
    x: list[float]

@app.get("/health")
def health():
    return {"status": "ok", "version": MODEL_VERSION}

@app.post("/predict")
def predict(data: Input):
    prediction = model.predict([data.x]).tolist()
    return {"prediction": prediction, "model_version": MODEL_VERSION}

 