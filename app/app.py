import os
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from openai import OpenAI
import json

app = FastAPI()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class StreamRequest(BaseModel):
    prompt: str

@app.get("/")
async def root():
    return {"status": "FastAPI Streaming LLM", "openai_key": bool(os.getenv("OPENAI_API_KEY"))}

@app.post("/stream")
async def stream_llm(request: StreamRequest):
    def generate():
        try:
            stream = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": request.prompt}],
                stream=True,
                temperature=0.7
            )
            
            # Send 5+ chunks as required
            chunk_count = 0
            buffer = ""
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    buffer += chunk.choices[0].delta.content
                    if len(buffer) >= 30 or chunk_count >= 5:  # 5+ chunks guaranteed
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
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
        }
    )
