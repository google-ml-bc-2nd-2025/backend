"""
공통으로 사용되는 환경 설정 및 구성 관리 모듈
"""

import os
import redis
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# LLM 관련 설정
DEFAULT_MODEL = os.getenv("MODEL", "gemma3:4b")  # 기본 Ollama 모델
OLLAMA_PORT = int(os.getenv("OLLAMA_PORT", 11434))

# Google AI 관련 설정
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_MODEL = os.getenv("GOOGLE_MODEL", "gemini-1.5-pro")

# 서비스 설정
DEFAULT_SERVICE = os.getenv("DEFAULT_SERVICE", "ollama")

# Redis 설정
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

# 싱글톤 패턴으로 Redis 클라이언트 생성
redis_client = None

def get_redis_client():
    """Redis 클라이언트 인스턴스를 반환합니다. 싱글톤 패턴 적용."""
    global redis_client
    
    if redis_client is not None:
        return redis_client
    
    try:
        # Redis 클라이언트 초기화
        client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            password=REDIS_PASSWORD,
            decode_responses=True
        )
        
        # Redis 연결 테스트
        client.ping()
        print("Redis 연결 성공")
        redis_client = client
        return client
    except Exception as e:
        print(f"Redis 연결 실패: {str(e)}")
        return None

# 환경 정보 출력 함수
def print_environment_info():
    """현재 환경 설정 정보를 출력합니다."""
    print("\n=== 환경 설정 정보 ===")
    print(f"기본 서비스: {DEFAULT_SERVICE}")
    print(f"Ollama 모델: {DEFAULT_MODEL}")
    
    if GOOGLE_API_KEY:
        print(f"Google AI 모델: {GOOGLE_MODEL}")
        print("Google API 키: 설정됨")
    else:
        print("Google API 키: 설정되지 않음")
    
    redis = get_redis_client()
    if redis:
        print(f"Redis 연결: {REDIS_HOST}:{REDIS_PORT}")
    else:
        print("Redis 연결: 사용 불가")
    print("===========================\n")