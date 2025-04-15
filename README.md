# GOBC Backend

Motion Generator 프로젝트의 백엔드 서버입니다.

## 구조

```
backend/
├── src/
│   ├── agents/          # Agent 관련 코드
│   │   ├── controller.py
│   │   └── task_executor.py
│   ├── api/            # FastAPI 엔드포인트
│   │   └── endpoints.py
│   ├── app.py         # FastAPI 애플리케이션
│   └── redis_client.py # Redis 클라이언트
└── tests/
    └── agents/        # 테스트 코드
        └── test_task_executor_integration.py
```

## 설치

```bash
pip install -r requirements.txt
```

## 실행

```bash
# FastAPI 서버 실행
uvicorn src.app:app --reload

# Celery 워커 실행 (별도 터미널에서)
celery -A src.celery_app worker --loglevel=info
```

## 테스트

```bash
pytest tests/
``` 