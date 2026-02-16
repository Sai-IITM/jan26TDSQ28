import os
from typing import Generator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
app = FastAPI(title="Streaming LLM API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class StreamRequest(BaseModel):
    prompt: str
    stream: bool = True

@app.get("/")
async def root():
    return {"message": "Streaming LLM API ready! POST to /stream"}

@app.post("/stream")
async def stream_llm(request: StreamRequest):
    # ... exact streaming generator code from before ...
    def event_generator() -> Generator[str, None, None]:
        try:
            stream = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": request.prompt}],
                stream=True
            )
            
            chunk_count = 0
            buffer = ""
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    buffer += chunk.choices[0].delta.content
                    
                    # Send every ~50 chars OR force 5 chunks minimum
                    if len(buffer) >= 50 or chunk_count >= 5:
                        yield f"data: {{\"content\": \"{buffer}\"}}\n\n"
                        buffer = ""
                        chunk_count += 1
            
            # Final buffer + DONE
            if buffer:
                yield f"data: {{\"content\": \"{buffer}\"}}\n\n"
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            yield f"data: {{\"error\": \"{str(e)}\"}}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

# Health check
@app.get("/")
async def root():
    return {"message": "Streaming LLM API ready! POST to /stream"}
