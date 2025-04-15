#!/bin/bash
set -e

# Ollama 서비스 시작
ollama serve &

# 모델 다운로드 대기 (서비스가 완전히 시작될 때까지)
echo "Ollama 서비스가 시작되기를 기다리는 중..."
sleep 5

# 필요한 모델 다운로드 (없는 경우)
echo "필요한 모델 다운로드 중..."
ollama pull gemma3:4b

# Python 애플리케이션 시작 (필요한 경우)
if [ -f "app.py" ]; then
    echo "애플리케이션 시작 중..."
    python3 app.py
else
    # 무한 대기 (컨테이너 실행 유지)
    echo "Ollama 서비스가 실행 중입니다. 컨테이너를 유지합니다."
    tail -f /dev/null
fi