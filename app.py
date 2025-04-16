from fastapi import FastAPI, HTTPException, Body
import uvicorn
from pydantic import BaseModel
from typing import Optional
import agent_manager
from agent.conf.config import (
    DEFAULT_MODEL, DEFAULT_SERVICE, GOOGLE_MODEL, GOOGLE_API_KEY,
    print_environment_info
)

app = FastAPI(title="ML Bootcamp API", version="0.1.0")

class PromptRequest(BaseModel):
    prompt: str
    model: Optional[str] = None
    stream: bool = False
    service: str = DEFAULT_SERVICE

@app.get("/api/health")
def health_check():
    """
    헬스 체크 엔드포인트
    """
    return {"status": "ok"}

@app.post("/api/generate")
def generate_text(request: PromptRequest):
    """
    지정된 서비스(Ollama 또는 Google AI)를 통해 텍스트 생성
    """
    try:
        # Google 모델을 사용하는 경우 서비스도 'google'로 강제 설정
        model = request.model or GOOGLE_MODEL
        service = request.service
        
        # 모델 이름이 Google 모델이면 서비스도 'google'로 설정
        if model == GOOGLE_MODEL:
            service = "google"
            print(f"Google 모델 {model}을 사용하므로 서비스를 'google'로 설정합니다.")
        
        print(f"사용할 서비스: {service}, 모델: {model}")
        
        result = agent_manager.generate_with_gemma3(
            prompt=request.prompt,
            model=model,
            stream=request.stream,
            service=service
        )
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        response_data = {
            "result": result.get("response", ""), 
            "model": model,
            "service": service
        }
        
        # 작업 ID가 있으면 응답에 포함
        if "task_id" in result:
            response_data["task_id"] = result["task_id"]
            
        return response_data
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/config")
def get_config():
    """
    현재 API 구성 정보 반환
    """
    google_available = bool(GOOGLE_API_KEY)
    
    return {
        "default_service": DEFAULT_SERVICE,
        "services": {
            "ollama": {
                "available": True,
                "default_model": DEFAULT_MODEL
            },
            "google": {
                "available": google_available,
                "default_model": GOOGLE_MODEL
            }
        }
    }

# 서버 시작 시 환경 정보 출력
@app.on_event("startup")
async def startup_event():
    print_environment_info()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=2188)