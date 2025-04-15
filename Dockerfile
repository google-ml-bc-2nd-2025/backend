FROM ollama/ollama:latest

# 필수 패키지 + 최신 pip 설치
RUN apt-get update && apt-get install -y curl python3-pip && \
    python3 -m pip install --upgrade pip setuptools wheel

# 디펜던시 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 실행
COPY . .
RUN chmod +x start.sh
CMD ["./start.sh"]