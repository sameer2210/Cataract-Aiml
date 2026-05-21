from fastapi import FastAPI, UploadFile, File

import shutil
import uuid
import os

from app.predictor import predict_image

app = FastAPI()

TEMP_DIR = "temp"

os.makedirs(TEMP_DIR, exist_ok=True)


@app.get("/")
def home():

    return {
        "message": "Cataract AI Running"
    }


@app.post("/predict")
async def predict(
    file: UploadFile = File(...)
):

    temp_path = (
        f"{TEMP_DIR}/{uuid.uuid4()}.png"
    )

    with open(temp_path, "wb") as buffer:

        shutil.copyfileobj(
            file.file,
            buffer
        )

    prediction, confidence = predict_image(
        temp_path
    )

    os.remove(temp_path)

    return {
        "prediction": prediction,
        "confidence": float(confidence)
    }