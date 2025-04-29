FROM python:3.12

# 비대화형 설치 환경 설정
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Asia/Seoul

# Google API 환경 변수 설정
ENV GOOGLE_API_KEY=${GOOGLE_API_KEY}
ENV GOOGLE_MODEL=gemini-1.5-pro
ENV DEFAULT_SERVICE=google

# MDM 서버 환경 변수 설정
ENV MDM_SERVER_URL=http://47.186.55.156:57179

# 작업 디렉토리 설정
WORKDIR /app

# 필요한 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    curl \
    dos2unix \    
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 구 pip 삭제 후 재설치
RUN apt-get remove -y python3-pip || true
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3

# Python 패키지 설치
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

RUN dos2unix start.sh
RUN chmod +x start.sh

# 포트 노출
EXPOSE 8000

# 시작 스크립트 실행
CMD ["./start.sh"]