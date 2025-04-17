# Backend

## 시스템 구조

### 1. API 엔드포인트
- `POST /api/prompt`: 프롬프트 수신 및 작업 생성
- `GET /api/tasks/{task_id}`: 작업 상태 확인

### 2. 비동기 작업 처리
- Celery + Redis를 사용한 비동기 작업 관리
- 작업 상태 추적 및 결과 저장

### 3. 에이전트 시스템 (LangGraph 기반)
```
backend/agent/
├── __init__.py          # 메인 에이전트 인터페이스
├── agent_graph.py       # 에이전트 워크플로우 정의
├── state.py            # 상태 관리
├── check_game_resource.py  # 리소스 요청 처리
├── think.py            # 사고 프로세스
├── research.py         # 정보 조사
├── work.py            # 작업 실행
└── answer.py          # 응답 생성
```

### 4. 모션 생성 모듈
- `mdm.py`: Motion Diffusion Model 인터페이스
  - 프롬프트 기반 모션 생성
  - SMPL 포맷 지원
  - 메타데이터 관리

## 작업 흐름

1. **프롬프트 수신**
   - 사용자가 프롬프트 전송
   - 작업 ID 생성 및 반환

2. **프롬프트 처리**
   - LangGraph 기반 에이전트가 프롬프트 분석
   - 모션 생성 요청 식별 및 처리

3. **모션 생성**
   - MDM 모델을 통한 모션 데이터 생성
   - SMPL 포맷으로 변환

4. **결과 반환**
   - 생성된 모션 데이터 저장
   - 작업 상태 업데이트

## 개발 현황

### 구현 완료
- ✅ FastAPI 기반 API 엔드포인트
- ✅ Celery + Redis 작업 큐
- ✅ MDM 인터페이스 기본 구조
- ✅ 에이전트 시스템 프레임워크

### 진행 중
- 🔄 모션 생성 에이전트 통합
- 🔄 프롬프트 처리 파이프라인

### 예정
- ⬜ Google API 통합 (번역/텍스트 정제)
- ⬜ 실제 MDM 모델 통합
- ⬜ 결과 저장 및 캐싱 시스템

## 환경 설정

### 필수 요구사항
- Python 3.8+
- Redis
- FastAPI
- Celery
- LangGraph

### 설치 및 실행
```bash
# 의존성 설치
pip install -r requirements.txt

# Redis 서버 실행
redis-server

# Celery 워커 실행
celery -A celery_app worker --loglevel=info

# API 서버 실행
uvicorn main:app --reload --port 8000
``` 