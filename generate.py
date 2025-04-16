"""
비동기 텍스트 생성 API 라우터 (Celery 통합)
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List
import logging
import os
from dotenv import load_dotenv
import google.generativeai as genai
from tasks import generate_text_async, process_batch_prompts

# 환경 변수 로드
load_dotenv()

# Google API 키 설정
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY가 설정되지 않았습니다. .env 파일을 확인해주세요.")

# Google AI 초기화
genai.configure(api_key=GOOGLE_API_KEY)

# 기본 설정
DEFAULT_MODEL = os.getenv("GOOGLE_MODEL", "gemini-1.5-pro")
DEFAULT_SERVICE = "google"

# 라우터 설정
router = APIRouter(prefix="/api", tags=["generate"])
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
@router.post("/generate")
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
@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """
    Celery 작업 상태 확인
    """
    try:
        task = generate_text_async.AsyncResult(task_id)
        if task.ready():
            return {
                "status": "completed",
                "result": task.get()
            }
        return {
            "status": "processing"
        }
    except Exception as e:
        logger.error(f"[Celery] 상태 확인 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# 배치 처리 API
@router.post("/generate/batch")
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
