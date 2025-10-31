from fastapi import FastAPI
from pydantic import BaseModel
import joblib

app = FastAPI()

model = joblib.load("model.pkl")

class TextInput(BaseModel):
    msg:str

@app.post("/predict")
def predict(data: TextInput):
    prediction = model.predict([data.msg])
    return {"sentiment": prediction}
