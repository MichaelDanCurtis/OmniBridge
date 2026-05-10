from fastapi import FastAPI


app = FastAPI(title="OmniBridge API")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
