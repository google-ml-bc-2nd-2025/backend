"""
FastAPI 메인 애플리케이션
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os
from dotenv import load_dotenv
import logging
from tasks import process_prompt

# 환경 변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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

# 요청 모델
class PromptRequest(BaseModel):
    prompt: str

# 프롬프트 엔드포인트
@app.post("/api/prompt")
async def handle_prompt(request: PromptRequest):
    """프롬프트를 처리하는 API 엔드포인트"""
    try:
        logger.info(f"[POST /api/prompt] 프롬프트 수신: {request.prompt}")
        
        # 프롬프트가 비어있는지 확인
        if not request.prompt.strip():
            raise HTTPException(
                status_code=400,
                detail={"message": "프롬프트가 비어있습니다"}
            )
        
        # 프롬프트 처리
        result = await process_prompt(request.prompt)
        
        if result['status'] == 'completed':
            return {
                "status": "success",
                "message": "프롬프트가 성공적으로 처리되었습니다",
                "refined_text": result['text_result'],
                "timing": result['timing']
            }
        else:
            raise HTTPException(
                status_code=500,
                detail={"message": result['error']}
            )
                
    except Exception as e:
        logger.error(f"프롬프트 처리 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"message": "프롬프트 처리 중 오류가 발생했습니다"}
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)