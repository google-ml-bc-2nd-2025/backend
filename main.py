"""
FastAPI 진입점 (LangGraph 기반 에이전트 연동)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from generate import router as generate_router  # generate.py 라우터 import
import logging
import os

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI 인스턴스 생성
app = FastAPI(title="LangGraph Agent API", version="1.0")

# CORS 설정 (프론트엔드와 연결 시 필요)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 배포 시에는 허용할 origin을 제한하세요
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(generate_router)

# 루트 경로 헬스체크
@app.get("/")
async def root():
    return {"status": "running", "message": "LangGraph Agent API is alive!"}


if __name__ == "__main__":
    import uvicorn

    reload = os.getenv("ENV", "dev") != "production"
    logger.info(f"Starting FastAPI server (reload={reload})")

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=reload)
