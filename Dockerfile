FROM ollama/ollama:latest


# 작업 디렉토리 설정
WORKDIR /app

# 필요한 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# 설치된 버전 확인
RUN python3 --version
RUN pip --version


# Python 패키지 설치
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# Ollama 서비스 시작 및 모델 다운로드를 위한 스크립트
COPY start.sh /start.sh
RUN chmod +x /start.sh

# 포트 노출 (Ollama API + 애플리케이션 포트)
EXPOSE 11434 8000

# 시작 스크립트 실행
ENTRYPOINT ["/start.sh"]