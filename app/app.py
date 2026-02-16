import os
import requests
import json
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

app = FastAPI()

class StreamRequest(BaseModel):
    prompt: str

@app.get("/")
async def root():
    return {"status": "AiPipe HTTP Streaming ✅", "ready": True}

@app.post("/stream")
async def stream_llm(request: StreamRequest):
    token = os.getenv("OPENAI_API_KEY")  # Your AiPipe JWT
    
    def generate():
        try:
            response = requests.post(
                "https://api.aipipe.ai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-3.5-turbo",
                    "messages": [{"role": "user", "content": request.prompt}],
                    "stream": True
                },
                stream=True
            )
            
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        data = line_str[6:]  # Remove "data: "
                        if data.strip() == '[DONE]':
                            yield "data: [DONE]\n\n"
                            break
                        yield f"{line_str}\n\n"
                        
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            yield "data: [DONE]\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")

