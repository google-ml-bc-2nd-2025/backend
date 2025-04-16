"""
LangGraph 기반 에이전트 구현
"""

import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 기본 모델 설정
DEFAULT_MODEL = os.getenv("MODEL", "gemma3:4b")

def answer_with_agent(prompt, model_name=DEFAULT_MODEL):
    """
    LangGraph 에이전트를 사용하여 답변 생성
    
    Args:
        prompt (str): 사용자 질문
        model_name (str): 사용할 모델 이름
        
    Returns:
        dict: 에이전트의 답변 결과
    """
    try:
        # 임시로 에코 응답 구현
        return {
            "answer": f"에이전트 응답: {prompt}",
            "model": model_name
        }
    except Exception as e:
        return {
            "error": f"에이전트 처리 중 오류 발생: {str(e)}"
        }

def streaming_agent_execution(prompt, model_name=DEFAULT_MODEL):
    """
    LangGraph 에이전트를 스트리밍 방식으로 실행
    
    Args:
        prompt (str): 사용자 질문
        model_name (str): 사용할 모델 이름
    """
    try:
        print(f"스트리밍 응답: {prompt}")
    except Exception as e:
        print(f"스트리밍 처리 중 오류 발생: {str(e)}") 