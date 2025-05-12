# ML Bootcamp API

이 프로젝트는 FastAPI를 기반으로 한 텍스트 생성 API 서비스입니다. Ollama와 Google AI 서비스를 지원하며, 다양한 AI 모델을 활용하여 텍스트를 생성할 수 있습니다.

## 주요 기능

- 텍스트 생성 API 엔드포인트 제공
- Ollama 및 Google AI 서비스 지원
- 스트리밍 응답 지원
- 헬스 체크 엔드포인트
- 설정 정보 조회 기능
- AI Agent 시스템 (LangGraph 기반)
  - 멀티 에이전트 협업
  - 워크플로우 자동화
  - 상태 관리 및 체크포인트

## 기술 스택

- FastAPI
- Uvicorn
- LangChain
- LangGraph
- Ollama
- Docker
- Redis

## 설치 및 실행

### 필수 요구사항

- Python 3.8 이상
- Docker 및 Docker Compose
- Ollama (로컬 실행 시)

### 환경 설정

1. 저장소 클론
```bash
git clone [repository-url]
cd [repository-name]
git checkout yk
```

2. 의존성 설치
```bash
pip install -r requirements.txt
```

3. 환경 변수 설정
`.env` 파일을 생성하고 필요한 환경 변수를 설정합니다:
```
GOOGLE_API_KEY=your_api_key
DEFAULT_MODEL=your_default_model
DEFAULT_SERVICE=ollama
```

### Docker를 사용한 실행

1. 도커 이미지 빌드 및 실행
```bash
docker-compose up --build
```

2. 백그라운드에서 실행
```bash
docker-compose up -d
```

3. 로그 확인
```bash
docker-compose logs -f
```

4. 서비스 중지
```bash
docker-compose down
```

### 도커 설정 상세

#### Dockerfile
- Python 3.12 기반
- 타임존: Asia/Seoul
- 포트: 2188
- 시작 스크립트: start.sh

#### docker-compose.yml
- 서비스:
  - fastapi: 메인 애플리케이션
  - redis: 캐시 서버
- 포트:
  - FastAPI: 2188
  - Redis: 6379

### 로컬 실행

```bash
./start.sh
```

## API 엔드포인트

### 1. 텍스트 생성
- **POST** `/api/generate`
- 요청 본문:
  ```json
  {
    "prompt": "생성할 텍스트 프롬프트",
    "model": "사용할 모델 (선택사항)",
    "stream": false,
    "service": "ollama 또는 google"
  }
  ```

### 2. 헬스 체크
- **GET** `/api/health`
- 서버 상태 확인

### 3. 설정 정보
- **GET** `/api/config`
- 현재 API 구성 정보 조회

## AI Agent 시스템

### LangGraph 기반 워크플로우
- 멀티 에이전트 협업 시스템
- 상태 관리 및 체크포인트 기능
- 비동기 처리 지원

### 주요 기능
1. 에이전트 관리
   - 에이전트 생성 및 설정
   - 상태 모니터링
   - 리소스 관리

2. 워크플로우 자동화
   - 작업 순차적 처리
   - 병렬 처리 지원
   - 에러 핸들링

3. 체크포인트 시스템
   - 작업 상태 저장
   - 복구 기능
   - 진행 상황 추적

## 프로젝트 구조

```
.
├── app.py              # FastAPI 애플리케이션 메인 파일
├── agent_manager.py    # 에이전트 관리 모듈
├── agent/             # 에이전트 관련 모듈
│   ├── conf/         # 설정 파일
│   ├── models/       # 에이전트 모델
│   └── workflows/    # 워크플로우 정의
├── Dockerfile         # 메인 Docker 설정
├── Dockerfile.base    # 기본 Docker 이미지 설정
├── docker-compose.yml # Docker Compose 설정
├── requirements.txt   # Python 의존성 목록
└── start.sh          # 서버 시작 스크립트
```

## 브랜치 정보

- `yk`: 최종 브랜치

## 라이선스

MIT License
