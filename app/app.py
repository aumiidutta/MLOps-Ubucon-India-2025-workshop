from fastapi import FastAPI
from pydantic import BaseModel
import joblib

app = FastAPI()

# Load model and vectorizer
model = joblib.load("model.pkl")
vectorizer = joblib.load("vectorizer.pkl")

class TextInput(BaseModel):
    msg: str

@app.post("/predict")
def predict(data: TextInput):
    text = data.msg
    text_vector = vectorizer.transform([text])

    prediction = model.predict(text_vector)
    result = prediction[0]

    return {"sentiment": str(result)}