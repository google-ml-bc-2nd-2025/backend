FROM ollama/ollama:latest

# 기본 도구 및 Python 업그레이드
RUN apt-get update && apt-get install -y \
    software-properties-common curl wget build-essential \
    python3.12 python3.12-dev python3.12-venv \
    && update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1 \
    && curl -sS https://bootstrap.pypa.io/get-pip.py | python3

# pip 업그레이드 및 디펜던시 설치
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# 애플리케이션 실행
COPY . .
RUN chmod +x start.sh
CMD ["./start.sh"]
