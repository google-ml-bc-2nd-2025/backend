"""
Celery 애플리케이션 설정
"""

from celery import Celery
import os
from datetime import timedelta

# Redis 연결 설정
REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
REDIS_PORT = os.getenv('REDIS_PORT', '6379')
REDIS_URL = f'redis://{REDIS_HOST}:{REDIS_PORT}/0'

# Celery 앱 생성
app = Celery(
    'animation_tasks',
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=['tasks']
)

# Celery 설정
app.conf.update(
    result_expires=timedelta(hours=24),  # 결과 24시간 유지
    task_track_started=True,  # 작업 시작 시간 추적
    task_time_limit=3600,  # 작업 제한 시간 1시간
    task_soft_time_limit=3000,  # 소프트 제한 시간 50분
    worker_prefetch_multiplier=1,  # 작업자당 한 번에 하나의 작업만 처리
    task_queue_max_priority=10,  # 우선순위 범위 (0-10)
    task_default_priority=5,  # 기본 우선순위
    task_create_missing_queues=True,  # 없는 큐 자동 생성
)

# 작업 큐 설정
task_queues = {
    'high_priority': {'routing_key': 'high', 'queue_arguments': {'x-max-priority': 10}},
    'default': {'routing_key': 'default', 'queue_arguments': {'x-max-priority': 5}},
    'low_priority': {'routing_key': 'low', 'queue_arguments': {'x-max-priority': 0}},
}

# 라우팅 설정
task_routes = {
    'tasks.generate_text_async': {'queue': 'default'},
    'tasks.process_batch_prompts': {'queue': 'low_priority'},
}

if __name__ == '__main__':
    app.start() 