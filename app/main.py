from fastapi import FastAPI

app = FastAPI(title="Devboard MCP Service")

@app.get("/health")
async def health():
    return {"status": "ok"}