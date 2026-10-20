from fastapi import FastAPI

app = FastAPI()


@app.get("/health", tags=["System"])
def health_check():
    return {"status": "alive"}
