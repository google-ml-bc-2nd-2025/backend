FROM python:3.12

# 비대화형 설치 환경 설정
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Asia/Seoul

# 작업 디렉토리 설정
WORKDIR /app

# 필요한 시스템 패키지 설치 (멀티 스테이지로 한번에 설치)
RUN apt-get update && apt-get install -y \
    curl \
    dos2unix \    
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 구 pip 삭제 후 재설치
# system pip 제거 (중요!)
RUN apt-get remove -y python3-pip || true

# 최신 pip 직접 설치 (pip, setuptools, wheel 포함)
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3

# 확인
RUN which pip3 && pip3 --version && python3 --version

# Python 패키지 설치 (requirements.txt를 별도로 복사해서 캐시 활용)
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사 (자주 변경되는 부분을 마지막에 배치)
COPY . .

RUN dos2unix start.sh
# Ollama 서비스 시작 스크립트 설정
RUN chmod +x start.sh

# 포트 노출 (서버 포트 , 2188)
EXPOSE 2188 2188

# 시작 스크립트 실행
CMD ["./start.sh"]