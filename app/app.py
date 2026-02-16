import os
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json

app = FastAPI()

class StreamRequest(BaseModel):
    prompt: str

@app.get("/")
async def root():
    return {"status": "FastAPI Streaming LLM (AiPipe)", "key_set": bool(os.getenv("OPENAI_API_KEY"))}

@app.post("/stream")
async def stream_llm(request: StreamRequest):
    # AiPipe uses OpenAI-compatible endpoint
    from openai import OpenAI
    client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),  # Your AiPipe key
        base_url="https://api.aipipe.ai/v1"   # AiPipe endpoint
    )
    
    def generate():
        try:
            stream = client.chat.completions.create(
                model="gpt-3.5-turbo",  # or whatever model AiPipe supports
                messages=[{"role": "user", "content": request.prompt}],
                stream=True
            )
            
            chunk_count = 0
            buffer = ""
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    buffer += chunk.choices[0].delta.content
                    if len(buffer) >= 30 or chunk_count >= 5:
                        yield f"data: {json.dumps({'content': buffer})}\n\n"
                        buffer = ""
                        chunk_count += 1
            
            if buffer:
                yield f"data: {json.dumps({'content': buffer})}\n\n"
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            yield "data: [DONE]\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")
