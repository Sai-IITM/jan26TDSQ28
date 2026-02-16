import os
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from openai import OpenAI

app = FastAPI()

# Debug endpoint
@app.get("/")
async def root():
    return {"status": "FastAPI Streaming LLM", "openai_key": bool(os.getenv("OPENAI_API_KEY"))}

class StreamRequest(BaseModel):
    prompt: str

@app.post("/stream")
async def stream_llm(request: StreamRequest):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    def generate():
        try:
            stream = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": request.prompt}],
                stream=True
            )
            for chunk in stream:
                content = chunk.choices[0].delta.content or ""
                if content:
                    yield f"data: {content}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: ERROR: {str(e)}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")

