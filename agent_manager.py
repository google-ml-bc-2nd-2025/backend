"""
Ollama 및 Google AI 클라이언트와 LangGraph 에이전트 통합 모듈
"""

import uuid
import datetime
import google.generativeai as genai
from agent import answer_with_agent, streaming_agent_execution
from agent.conf.config import (
    DEFAULT_MODEL, DEFAULT_SERVICE, GOOGLE_MODEL, GOOGLE_API_KEY,
    get_redis_client, print_environment_info
)

# Redis 클라이언트 가져오기
redis_client = get_redis_client()

# Google AI 초기화 (API 키가 있는 경우)
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

def log_request_to_redis(task_id, service, model, prompt):
    """
    Redis에 요청 기록 저장
    
    Args:
        task_id (str): 작업 식별자 (UUID)
        service (str): 사용된 서비스 (ollama 또는 google)
        model (str): 사용된 모델 이름
        prompt (str): 요청된 프롬프트
    """
    if redis_client is None:
        return
    
    try:
        timestamp = datetime.datetime.now().isoformat()
        log_data = {
            "task_id": task_id,
            "timestamp": timestamp,
            "service": service,
            "model": model,
            "prompt": prompt,
            "status": "requested"
        }
        
        # Redis에 로그 저장 (JSON 형식)
        redis_client.hset(f"task:{task_id}", mapping=log_data)
        
        # 로그 메시지 저장
        log_message = f"{timestamp}: [{task_id}] {model}에 '{prompt}' 요청"
        redis_client.lpush("request_logs", log_message)
        redis_client.ltrim("request_logs", 0, 999)  # 최대 1000개 로그 유지
        
        print(f"Redis에 작업 기록 저장: {task_id}")
    except Exception as e:
        print(f"Redis 로깅 실패: {str(e)}")

def update_task_status(task_id, status, response=None):
    """
    Redis에 작업 상태 업데이트
    
    Args:
        task_id (str): 작업 식별자 (UUID)
        status (str): 작업 상태 (completed, failed)
        response (str, optional): 응답 결과
    """
    if redis_client is None:
        return
    
    try:
        # 기존 데이터 가져오기
        task_data = redis_client.hgetall(f"task:{task_id}")
        if not task_data:
            return
        
        # 상태 업데이트
        task_data["status"] = status
        task_data["completed_at"] = datetime.datetime.now().isoformat()
        
        if response:
            task_data["response"] = response[:1000]  # 응답이 너무 길면 자르기
        
        # Redis 업데이트
        redis_client.hset(f"task:{task_id}", mapping=task_data)
        
        # 완료 로그 추가
        log_message = f"{task_data['completed_at']}: [{task_id}] {status}"
        redis_client.lpush("request_logs", log_message)
        redis_client.ltrim("request_logs", 0, 999)
    except Exception as e:
        print(f"Redis 상태 업데이트 실패: {str(e)}")

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
    # UUID 생성
    task_id = str(uuid.uuid4())
    
    # Redis에 요청 기록 저장
    log_request_to_redis(task_id, service, model, prompt)
    
    try:
        if service.lower() == "google":
            result = generate_with_google_ai(prompt, model, stream)
        else:  # 기본값은 ollama
            result = generate_with_ollama(prompt, model, stream)
        
        # 성공 상태 업데이트
        if "response" in result:
            update_task_status(task_id, "completed", result["response"])
        else:
            update_task_status(task_id, "failed", result.get("error", "알 수 없는 오류"))
        
        # 결과에 task_id 추가
        result["task_id"] = task_id
        return result
    except Exception as e:
        error_msg = f"생성 중 오류 발생: {str(e)}"
        # 실패 상태 업데이트
        update_task_status(task_id, "failed", error_msg)
        return {"error": error_msg, "task_id": task_id}

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
    
    # 환경 설정 정보 출력
    print_environment_info()
    
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