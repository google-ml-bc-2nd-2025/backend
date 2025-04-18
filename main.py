"""
FastAPI 메인 애플리케이션
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import os
from dotenv import load_dotenv
import logging
from generate import generate_with_retry, refine_prompt
from tasks import generate_text_async, process_batch_prompts

# 환경 변수 로드
load_dotenv()

# 기본 설정
DEFAULT_MODEL = os.getenv("GOOGLE_MODEL", "gemini-1.5-pro")
DEFAULT_SERVICE = "google"
AI_MODEL_SERVER_URL = os.getenv("AI_MODEL_SERVER_URL", "http://localhost:8002")

# FastAPI 앱 생성
app = FastAPI(title="Motion Generation API")

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 요청 모델
class PromptRequest(BaseModel):
    prompt: str
    model: Optional[str] = DEFAULT_MODEL
    stream: Optional[bool] = False
    service: Optional[str] = DEFAULT_SERVICE

class BatchPromptRequest(BaseModel):
    prompts: List[str]
    model: Optional[str] = DEFAULT_MODEL
    service: Optional[str] = DEFAULT_SERVICE

# 단일 생성 API (비동기)
@app.post("/api/generate")
async def generate_text(request: PromptRequest):
    """
    비동기적으로 텍스트 생성
    """
    try:
        logger.info(f"[POST /api/generate] 질문 수신: {request.prompt}")
        
        # Celery 작업 시작
        task = generate_text_async.delay(
            prompt=request.prompt,
            model=request.model,
            stream=request.stream,
            service=request.service
        )
        
        return {
            "task_id": task.id,
            "status": "processing"
        }

    except Exception as e:
        logger.error(f"[Celery] 생성 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# 작업 상태 확인 API
@app.get("/api/tasks/{task_id}")
async def get_task_status(task_id: str):
    """
    Celery 작업 상태 확인
    """
    try:
        task = generate_text_async.AsyncResult(task_id)
        if task.ready():
            result = task.get()
            
            if result.get("status") == "completed":
                return {
                    "status": "completed",
                    "text_result": result["text_result"],
                    "animation_result": result["animation_result"]
                }
            elif result.get("status") == "text_only":
                return {
                    "status": "text_only",
                    "text_result": result["text_result"],
                    "animation_error": result["animation_error"]
                }
            else:
                return {
                    "status": "failed",
                    "error": result.get("error", "Unknown error occurred")
                }
                
        return {
            "status": "processing"
        }
    except Exception as e:
        logger.error(f"[Celery] 상태 확인 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# 배치 처리 API
@app.post("/api/generate/batch")
async def generate_batch(request: BatchPromptRequest):
    """
    여러 프롬프트를 배치로 처리
    """
    try:
        logger.info(f"[POST /api/generate/batch] 배치 요청 수신: {len(request.prompts)} 개")
        
        # Celery 배치 작업 시작
        task = process_batch_prompts.delay(
            prompts=request.prompts,
            model=request.model,
            service=request.service
        )
        
        return {
            "task_id": task.id,
            "status": "processing",
            "total_prompts": len(request.prompts)
        }

    except Exception as e:
        logger.error(f"[Celery] 배치 처리 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# 프롬프트 엔드포인트 추가
@app.post("/api/prompt")
async def process_prompt(request: Request):
    """프롬프트를 처리하는 API 엔드포인트"""
    data = await request.json()
    prompt = data.get("prompt", "")
    
    logger.info(f"[POST /api/prompt] 프롬프트 수신: {prompt}")
    
    try:
        # Celery 작업 시작
        task = generate_text_async.delay(
            prompt=prompt,
            model=DEFAULT_MODEL,
            stream=False,
            service=DEFAULT_SERVICE
        )
        
        return {
            "status": "success",
            "prompt": prompt,
            "message": "프롬프트가 처리되었습니다.",
            "task_id": task.id,
            "check_status_url": f"/api/tasks/{task.id}"
        }
                
    except Exception as e:
        logger.error(f"프롬프트 처리 중 오류 발생: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
