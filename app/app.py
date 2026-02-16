import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from openai import OpenAI

app = FastAPI()

# Test OpenAI connection
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class StreamRequest(BaseModel):
    prompt: str

@app.get("/")
async def root():
    try:
        client.models.list()  # Test API key
        return {"status": "OK", "openai": "connected"}
    except Exception as e:
        return {"status": "ERROR", "openai": str(e)}

@app.post("/stream")
async def stream_llm(request: StreamRequest):
    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(500, "OPENAI_API_KEY missing")
    
    try:
        stream = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": request.prompt}],
            stream=True
        )
        
        def generate():
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield f"data: {chunk.choices[0].delta.content}\n\n"
            yield "data: [DONE]\n\n"
        
        return StreamingResponse(generate(), media_type="text/event-stream")
    except Exception as e:
        raise HTTPException(500, str(e))

