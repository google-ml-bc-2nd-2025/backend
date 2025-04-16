from celery import Celery
import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# Redis 설정
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = os.getenv('REDIS_PORT', '6379')
REDIS_DB = os.getenv('REDIS_DB', '0')

# Celery 앱 생성
app = Celery(
    'backend',
    broker=f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}',
    backend=f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}',
    include=['tasks']  # tasks.py에 정의된 작업들을 포함
)

# Celery 설정
app.conf.update(
    result_expires=3600,  # 결과 유효 시간 1시간
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Seoul',
    enable_utc=True,
) 