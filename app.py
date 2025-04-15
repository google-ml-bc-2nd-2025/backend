from fastapi import FastAPI, HTTPException, Body
import uvicorn
from pydantic import BaseModel
from typing import Optional
import ollama_client
from dotenv import load_dotenv
import os

# .env 파일 로드
load_dotenv()

# 환경 변수에서 MODEL 값 가져오기
DEFAULT_MODEL = os.getenv("MODEL", "gemma3:4b")

app = FastAPI(title="ML Bootcamp API", version="0.1.0")

class PromptRequest(BaseModel):
    prompt: str
    model: str = DEFAULT_MODEL
    stream: bool = False

@app.get("/api/health")
def health_check():
    """
    헬스 체크 엔드포인트
    """
    return {"status": "ok"}

@app.post("/api/generate")
def generate_text(request: PromptRequest):
    """
    Ollama API를 통해 Gemma 3 모델로 텍스트 생성
    """
    try:
        result = ollama_client.generate_with_gemma3(
            prompt=request.prompt, 
            model=request.model,
            stream=request.stream
        )
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return {"result": result.get("response", ""), "model": request.model}
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=2188)