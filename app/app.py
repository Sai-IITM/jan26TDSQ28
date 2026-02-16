import os
import json
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from openai import OpenAI

app = FastAPI()

class StreamRequest(BaseModel):
    prompt: str

@app.get("/")
async def root():
    return {"status": "AiPipe Streaming LLM ✅", "ready": True}

@app.post("/stream")
async def stream_llm(request: StreamRequest):
    # AiPipe OpenAI-compatible client
    client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),  # Your JWT token
        base_url="https://api.aipipe.ai/v1"  # AiPipe endpoint
    )
    
    def generate():
        try:
            stream = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": request.prompt}],
                stream=True
            )
            
            # Assignment requirement: 5+ chunks
            chunk_count = 0
            buffer = ""
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    buffer += chunk.choices[0].delta.content
                    # Send chunks of ~30 chars OR force 5 chunks
                    if len(buffer) >= 30 or chunk_count >= 5:
                        yield f"data: {json.dumps({'content': buffer})}\n\n"
                        buffer = ""
                        chunk_count += 1
            
            # Final chunk
            if buffer:
                yield f"data: {json.dumps({'content': buffer})}\n\n"
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )


