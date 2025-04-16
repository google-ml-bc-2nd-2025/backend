"""
LangGraph 기반 텍스트 생성 API 라우터
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging
import os
from dotenv import load_dotenv
import google.generativeai as genai

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
DEFAULT_SERVICE = "google"  # 기본 서비스를 google로 설정

# 라우터 설정
router = APIRouter(prefix="/api", tags=["generate"])
logger = logging.getLogger(__name__)

# 요청 모델
class PromptRequest(BaseModel):
    prompt: str
    model: Optional[str] = DEFAULT_MODEL
    stream: Optional[bool] = False
    service: Optional[str] = DEFAULT_SERVICE

# 생성 API
@router.post("/generate")
async def generate_text(request: PromptRequest):
    """
    Google AI를 통해 텍스트 생성
    """
    try:
        logger.info(f"[POST /api/generate] 질문 수신: {request.prompt}")
        
        # Google AI 모델 설정
        model = genai.GenerativeModel(request.model)
        
        # 텍스트 생성
        response = model.generate_content(request.prompt)
        
        return {
            "result": response.text,
            "model": request.model,
            "service": request.service
        }

    except Exception as e:
        logger.error(f"[Google AI] 생성 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
