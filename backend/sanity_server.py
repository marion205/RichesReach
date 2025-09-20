from fastapi import FastAPI
import uvicorn, os
from datetime import datetime

app = FastAPI()
BUILD = "sanity-" + datetime.now().isoformat(timespec="seconds")

@app.get("/")
def root():
    return {"ok": True, "build": BUILD}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8124)))
