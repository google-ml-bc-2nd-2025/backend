#!/bin/bash
set -e

# Ollama 서비스 시작
echo "Ollama 서비스 시작 중..."
ollama serve &
OLLAMA_PID=$!

# 서비스가 준비될 때까지 기다림 (고정 대기 시간 대신 실제 준비 상태 확인)
echo "Ollama 서비스가 준비될 때까지 기다리는 중..."
max_attempts=30
attempt=0
while ! curl -s http://localhost:11434/api/tags >/dev/null 2>&1; do
    attempt=$((attempt + 1))
    if [ $attempt -ge $max_attempts ]; then
        echo "Ollama 서비스 시작 시간 초과"
        exit 1
    fi
    echo "Ollama API를 기다리는 중... ($attempt/$max_attempts)"
    sleep 2
done

echo "Ollama 서비스 준비 완료!"

# 필요한 모델 확인 및 다운로드
MODEL=$(grep -oP 'MODEL="\K[^"]+' .env 2>/dev/null || echo "gemma3:4b")
echo "모델 '$MODEL' 확인 중..."
if ! ollama list | grep -q "$MODEL"; then
    echo "모델 '$MODEL' 다운로드 중..."
    ollama pull $MODEL
else
    echo "모델 '$MODEL'이(가) 이미 존재합니다."
fi

# Python 애플리케이션 시작
if [ -f "app.py" ]; then
    echo "백엔드 애플리케이션 시작 중..."
    exec python3 app.py
else
    # 무한 대기 (컨테이너 실행 유지)
    echo "Ollama 서비스만 실행 중입니다. 컨테이너를 유지합니다."
    
    # Ollama 프로세스 종료 시 컨테이너도 종료하도록 설정
    wait $OLLAMA_PID
fi