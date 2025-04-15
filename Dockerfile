FROM bc_backend:1.1

# 비대화형 설치 환경 설정
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Asia/Seoul

# 작업 디렉토리 설정
WORKDIR /app

# 필요한 시스템 패키지 설치 (멀티 스테이지로 한번에 설치)
RUN apt-get update && apt-get install -y \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Python 패키지 설치 (requirements.txt를 별도로 복사해서 캐시 활용)
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사 (자주 변경되는 부분을 마지막에 배치)
COPY . .

# Ollama 서비스 시작 스크립트 설정
COPY start.sh /start.sh
RUN chmod +x /start.sh

# 포트 노출 (Ollama API + 애플리케이션 포트)
EXPOSE 11434 8000

# 시작 스크립트 실행
ENTRYPOINT ["/start.sh"]