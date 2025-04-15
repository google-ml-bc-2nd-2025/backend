import os
from dotenv import load_dotenv
from langchain_ollama import OllamaLLM
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

# .env 파일 로드
load_dotenv()

PORT = 11434
# 환경 변수에서 MODEL 값 가져오기
DEFAULT_MODEL = os.getenv("MODEL", "gemma3:4b")  # 기본값은 "gemma3:4b"

def create_ollama_llm(model_name=DEFAULT_MODEL, streaming=False):
    """LangChain Ollama LLM 생성"""
    callbacks = [StreamingStdOutCallbackHandler()] if streaming else []
    return OllamaLLM(
        model=model_name,
        base_url=f"http://localhost:{PORT}",
        callbacks=callbacks
    )