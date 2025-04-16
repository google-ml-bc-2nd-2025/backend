"""
Ollama 및 Google AI 클라이언트와 LangGraph 에이전트 통합 모듈
"""

import os
from dotenv import load_dotenv
from agent import answer_with_agent, streaming_agent_execution, DEFAULT_MODEL
import google.generativeai as genai

# .env 파일 로드
load_dotenv()

# Google API 키 로드
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
# 기본 서비스 설정 (ollama 또는 google)
DEFAULT_SERVICE = os.getenv("DEFAULT_SERVICE", "ollama")
# Google 모델 설정
GOOGLE_MODEL = os.getenv("GOOGLE_MODEL", "gemini-1.5-pro")

# Google AI 초기화 (API 키가 있는 경우)
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

def generate_with_gemma3(prompt, model=DEFAULT_MODEL, stream=False, service=DEFAULT_SERVICE):
    """
    선택한 서비스(Ollama 또는 Google AI)를 사용하여 텍스트 생성
    
    Args:
        prompt (str): 모델에 전송할 프롬프트 텍스트
        model (str): 사용할 모델 이름 (기본값: .env의 MODEL 값)
        stream (bool): 스트리밍 응답 여부
        service (str): 사용할 서비스 - 'ollama' 또는 'google' (기본값: .env의 DEFAULT_SERVICE 값)
        
    Returns:
        dict: 모델의 응답 결과
    """
    try:
        if service.lower() == "google":
            return generate_with_google_ai(prompt, model, stream)
        else:  # 기본값은 ollama
            return generate_with_ollama(prompt, model, stream)
    except Exception as e:
        return {"error": f"생성 중 오류 발생: {str(e)}"}

def generate_with_ollama(prompt, model=DEFAULT_MODEL, stream=False):
    """
    Ollama를 사용하여 텍스트 생성
    
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
        return {"error": f"Ollama 생성 중 오류 발생: {str(e)}"}

def generate_with_google_ai(prompt, model=GOOGLE_MODEL, stream=False):
    """
    Google AI 서비스를 사용하여 텍스트 생성
    
    Args:
        prompt (str): 모델에 전송할 프롬프트 텍스트
        model (str): 사용할 Google AI 모델 이름 (기본값: .env의 GOOGLE_MODEL 값)
        stream (bool): 스트리밍 응답 여부
        
    Returns:
        dict: 모델의 응답 결과
    """
    if not GOOGLE_API_KEY:
        return {"error": "Google API 키가 설정되지 않았습니다. .env 파일에 GOOGLE_API_KEY를 추가하세요."}
    
    try:
        # Google Generative AI 모델 설정
        genai_model = genai.GenerativeModel(model)
        
        if stream:
            # 스트리밍 방식 응답
            response = genai_model.generate_content(prompt, stream=True)
            streaming_result = ""
            
            for chunk in response:
                if hasattr(chunk, 'text'):
                    streaming_result += chunk.text
            
            return {
                "response": streaming_result,
                "done": True
            }
        else:
            # 일반 응답 방식
            response = genai_model.generate_content(prompt)
            return {
                "response": response.text,
                "done": True
            }
    except Exception as e:
        return {"error": f"Google AI 생성 중 오류 발생: {str(e)}"}

if __name__ == "__main__":
    print("=== AI 서비스와 LangGraph 에이전트 사용하기 ===\n")
    
    # 사용할 서비스 (ollama 또는 google)
    service = os.getenv("DEFAULT_SERVICE", "ollama")
    print(f"사용 중인 서비스: {service.upper()}")
    
    # 1. 기본 에이전트 답변 (Ollama)
    question1 = "3D 캐릭터 모델을 만들어줘"
    print(f"질문: {question1}")
    print("\n--- Ollama 에이전트 답변 ---")
    result = answer_with_agent(question1)
    print(f"최종 답변: {result['answer']}")
    
    # 2. Google AI 서비스 테스트 (API 키가 있는 경우)
    if GOOGLE_API_KEY:
        print("\n\n=== Google AI 서비스 테스트 ===")
        question2 = "걷는 애니메이션을 만들어줘"
        print(f"질문: {question2}")
        result = generate_with_google_ai(question2)
        print(f"Google AI 답변: {result['response']}")
    
    # 3. 스트리밍 방식으로 에이전트 실행 과정 보기
    print("\n\n=== 스트리밍 방식으로 에이전트 실행 ===")
    question3 = "걷는 애니메이션을 만들어줘"
    streaming_agent_execution(question3)
    
    # 4. 처리할 수 없는 요청 테스트
    print("\n\n=== 처리할 수 없는 요청 테스트 ===")
    question4 = "어제 날씨는 어땠어?"
    streaming_agent_execution(question4)