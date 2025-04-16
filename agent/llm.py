"""
LLM 모델 생성 및 관리를 위한 모듈
"""

from langchain_ollama import OllamaLLM
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from agent.conf.config import DEFAULT_MODEL, OLLAMA_PORT

def create_ollama_llm(model_name=DEFAULT_MODEL, streaming=False):
    """LangChain Ollama LLM 생성"""
    callbacks = [StreamingStdOutCallbackHandler()] if streaming else []
    return OllamaLLM(
        model=model_name,
        base_url=f"http://localhost:{OLLAMA_PORT}",
        callbacks=callbacks
    )