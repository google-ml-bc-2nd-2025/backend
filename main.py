"""
FastAPI 메인 애플리케이션
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os
from dotenv import load_dotenv
import logging
from generate import generate_with_retry, refine_prompt
from tasks import generate_text_async
from agent.think import check_prompt
import json
import base64
import numpy as np
import redis

# 환경 변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Redis 클라이언트 초기화
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "redis"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    db=int(os.getenv("REDIS_DB", 0)),
    decode_responses=False,
    socket_timeout=5,
    socket_connect_timeout=5
)

# Redis 연결 테스트
try:
    redis_client.ping()
    logger.info("Redis 연결 성공")
except redis.ConnectionError as e:
    logger.error(f"Redis 연결 실패: {str(e)}")
    raise Exception("Redis 서버에 연결할 수 없습니다. Redis가 실행 중인지 확인해주세요.")

# 기본 설정
DEFAULT_MODEL = os.getenv("GOOGLE_MODEL", "gemini-1.5-pro")
DEFAULT_SERVICE = "google"

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
    model: Optional[str] = DEFAULT_MODEL
    stream: Optional[bool] = False
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
        current_state = task.state

        logger.info(f"작업 상태 확인: task_id={task_id}, state={current_state}")
        
        if current_state == "SUCCESS":
            #모션 데이터 조회
            motion_key = f"motion:{task_id}"
            motion_data = redis_client.get(motion_key)

            if motion_data == None:
                logger.error(f"작업 결과가 None입니다. task_id: {task_id}")
                return {
                    "status": "failed",
                    "message": "작업 결과가 존재하지 않습니다 (None)"
                }

            return {
                "status": "completed",
                "message": "작업이 완료되었습니다",
                "data": {
                    "text": task.result.get("text_result", ""),
                    "motion": motion_data
                }
            }

        elif current_state == "PENDING" or current_state == "STARTED":
            return {
                "status": "processing",
                "message": "작업 처리 중..."
            }
            
        else:
            logger.warning(f"작업 상태 확인 중: {current_state}")
            return {
                "status": "processing",
                "message": f"작업 상태: {current_state}"
            }
    
    except Exception as e:
        logger.error(f"작업 상태 확인 중 오류 발생: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
        
# 프롬프트 엔드포인트 추가
@app.post("/api/prompt")
async def process_prompt(request: Request):
    """프롬프트를 처리하는 API 엔드포인트"""
    data = await request.json()
    prompt = data.get("prompt", "")
    
    logger.info(f"[POST /api/prompt] 프롬프트 수신: {prompt}")
    
    try:
        # 프롬프트 검사
        prompt_state = check_prompt(prompt)
        if not prompt_state.is_valid:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "프롬프트가 비어있습니다"
                }
            )
        
        # Celery 작업 시작
        task = generate_text_async.delay(prompt)
        
        return {"task_id": task.id}
                
    except Exception as e:
        logger.error(f"프롬프트 처리 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"message": "프롬프트 처리 중 오류가 발생했습니다"}
        )

@app.get("/api/motion/{task_id}")
async def get_motion_data(task_id: str):
    """모션 데이터를 조회합니다."""
    try:     
        # Redis에서 모션 데이터 조회
        motion_key = f"motion:{task_id}"
        motion_data = redis_client.get(motion_key)

        if motion_data is None:
            raise HTTPException(status_code=404, detail="모션 데이터를 찾을 수 없습니다")
        
        #데이터 처리
        motion_dict = json.loads(motion_data)
        data_bytes = base64.b64decode(motion_dict["data"])
        motion_array = np.frombuffer(data_bytes, dtype=np.dtype(motion_dict["dtype"])).reshape(motion_dict["shape"])

        return {"smpl_data": motion_array.tolist()}
        
    except Exception as e:
        logger.error(f"모션 데이터 조회 실패: task_id={task_id}, error={str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))