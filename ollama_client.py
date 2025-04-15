"""
Ollama 클라이언트 및 LangGraph 에이전트 통합 모듈
"""

import os
from dotenv import load_dotenv
from agent import answer_with_agent, streaming_agent_execution, DEFAULT_MODEL

# .env 파일 로드
load_dotenv()

def generate_with_gemma3(prompt, model=DEFAULT_MODEL, stream=False):
    """
    Gemma 모델을 사용하여 텍스트 생성
    
    Args:
        prompt (str): 모델에 전송할 프롬프트 텍스트
        model (str): 사용할 모델 이름 (기본값: .env의 MODEL 값)
        stream (bool): 스트리밍 응답 여부
        
    Returns:
        dict: 모델의 응답 결과
    """
    try:
        if stream:
            # 스트리밍 방식은 현재 API에서 처리하기 어려우므로
            # 일반 방식으로 처리 후 결과만 반환
            result = answer_with_agent(prompt, model_name=model)
            return {
                "response": result["answer"],
                "done": True
            }
        else:
            # 일반 응답 방식
            result = answer_with_agent(prompt, model_name=model)
            return {
                "response": result["answer"],
                "done": True
            }
    except Exception as e:
        return {"error": f"생성 중 오류 발생: {str(e)}"}

if __name__ == "__main__":
    print("=== LangGraph로 Ollama 에이전트 사용하기 ===\n")
    
    # 1. 기본 에이전트 답변
    question1 = "3D 캐릭터 모델을 만들어줘"
    print(f"질문: {question1}")
    print("\n--- 에이전트 답변 ---")
    result = answer_with_agent(question1)
    print(f"최종 답변: {result['answer']}")
    
    # 2. 스트리밍 방식으로 에이전트 실행 과정 보기
    print("\n\n=== 스트리밍 방식으로 에이전트 실행 ===")
    question2 = "걷는 애니메이션을 만들어줘"
    streaming_agent_execution(question2)
    
    # 3. 처리할 수 없는 요청 테스트
    print("\n\n=== 처리할 수 없는 요청 테스트 ===")
    question3 = "어제 날씨는 어땠어?"
    streaming_agent_execution(question3)