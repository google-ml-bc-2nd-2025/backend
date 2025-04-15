import os
import json
import re
from typing import Dict, TypedDict, List, Annotated, Sequence, Literal, Optional, Union
# dotenv 임포트 추가
from dotenv import load_dotenv
# 새로운 임포트 사용
from langchain_ollama import OllamaLLM
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain_core.prompts import PromptTemplate
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

# .env 파일 로드
load_dotenv()

PORT = 11434
# 환경 변수에서 MODEL 값 가져오기
DEFAULT_MODEL = os.getenv("MODEL", "gemma3:4b")  # 기본값은 "gemma3:4b"

# 상태 타입 정의
class AgentState(TypedDict):
    question: str
    thoughts: List[str]
    research_results: str
    answer: str
    is_game_resource_request: bool
    resource_type: Optional[str]
    resource_details: Dict[str, str]
    work_results: Optional[str]
    next: str

def create_ollama_llm(model_name=DEFAULT_MODEL, streaming=False):
    """LangChain Ollama LLM 생성"""
    callbacks = [StreamingStdOutCallbackHandler()] if streaming else []
    return OllamaLLM(
        model=model_name,
        base_url=f"http://localhost:{PORT}",
        callbacks=callbacks
    )

def check_game_resource_request(state: AgentState) -> AgentState:
    """게임 리소스 제작 요청인지 확인"""
    llm = create_ollama_llm()
    prompt = PromptTemplate.from_template(
        """사용자의 질문이 게임 리소스(3D 모델 또는 애니메이션) 제작 요청인지 분석하세요.
        
        질문: {question}
        
        다음 정보를 JSON 형식으로 응답하세요:
        1. is_game_resource_request: 게임 리소스 제작 요청인지 여부 (true/false)
        2. resource_type: 요청된 리소스 유형 ("3d_model", "animation", "other" 중 하나)
        3. 요청된 리소스의 세부 정보 (캐릭터 이름, 스타일, 포즈 등)
        
        JSON 형식 응답:"""
    )
    
    analysis = llm.invoke(prompt.format(question=state["question"]))
    
    try:
        json_match = re.search(r'(\{.*\})', analysis, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
            analysis_dict = json.loads(json_str)
        else:
            analysis_dict = json.loads(analysis)
    except:
        analysis_dict = {
            "is_game_resource_request": False,
            "resource_type": "other",
            "details": {}
        }
    
    is_valid_request = (analysis_dict.get("is_game_resource_request", False) and 
                        analysis_dict.get("resource_type") in ["3d_model", "animation"])
    
    next_step = "think" if is_valid_request else "reject_request"
    
    return {
        **state,
        "is_game_resource_request": analysis_dict.get("is_game_resource_request", False),
        "resource_type": analysis_dict.get("resource_type", "other"),
        "resource_details": analysis_dict.get("details", {}),
        "next": next_step
    }

def reject_request(state: AgentState) -> AgentState:
    """게임 리소스 요청이 아닌 경우 거부 메시지 생성"""
    return {
        **state,
        "answer": "지금은 3D 모델과 애니메이션 제작 요청만 가능합니다.",
        "next": END
    }

def think(state: AgentState) -> AgentState:
    """사고 단계: 질문을 분석하고 접근 방법 결정"""
    llm = create_ollama_llm()
    prompt = PromptTemplate.from_template(
        """질문을 분석하고 애니메이션 제작에 대한 사고 과정을 설명하세요.:
        
        질문: {question}
        
        사고 과정:"""
    )
    
    thoughts = llm.invoke(prompt.format(question=state["question"]))
    
    return {
        **state,
        "thoughts": state.get("thoughts", []) + [thoughts],
        "next": "research_step"
    }

def research(state: AgentState) -> AgentState:
    """연구 단계: 질문에 대한 정보 수집"""
    llm = create_ollama_llm()
    
    if state.get("is_game_resource_request", False):
        prompt = PromptTemplate.from_template(
            """사용자가 게임 리소스 제작을 요청했습니다. 다음 정보를 바탕으로 제작 방법과 단계를 상세히 설명하세요:
            
            요청 유형: {resource_type}
            요청 세부 정보: {resource_details}
            
            다음 내용을 포함해주세요:
            1. 필요한 소프트웨어와 도구
            2. 제작 단계와 프로세스
            3. 일반적인 기술적 고려사항
            4. 작업 시간 추정
            
            자세한 조사 결과:"""
        )
        
        resource_type = "3D 모델" if state["resource_type"] == "3d_model" else "애니메이션"
        research_results = llm.invoke(
            prompt.format(
                resource_type=resource_type,
                resource_details=json.dumps(state["resource_details"], ensure_ascii=False)
            )
        )
    else:
        prompt = PromptTemplate.from_template(
            """질문에 대한 정보를 조사하고 수집하세요:
            
            질문: {question}
            지금까지 사고: {thoughts}
            
            조사 결과:"""
        )
        
        research_results = llm.invoke(
            prompt.format(
                question=state["question"],
                thoughts="\n".join(state["thoughts"])
            )
        )
    
    return {
        **state,
        "research_results": research_results,
        "next": "work_step" if state.get("is_game_resource_request", False) else "answer_step"
    }

def work_step(state: AgentState) -> AgentState:
    """작업 단계: 실제 게임 리소스 생성 작업 수행"""
    resource_type = state.get("resource_type", "other")
    
    if resource_type == "3d_model":
        work_results = """
        [3D 모델 생성 결과]
        - 파일 형식: FBX, OBJ, GLTF
        - 폴리곤 수: 15,420
        - 텍스처 맵: Diffuse, Normal, Roughness, Metallic
        - 리깅: 완료
        - 미리보기 URL: https://example.com/preview/model123.jpg
        - 다운로드 URL: https://example.com/download/model123.zip
        
        모델이 성공적으로 생성되었습니다. 위 URL에서 확인하고 다운로드할 수 있습니다.
        """
    elif resource_type == "animation":
        work_results = """
        [애니메이션 생성 결과]
        - 파일 형식: FBX, BVH
        - 프레임 수: 120
        - 애니메이션 길이: 4초
        - 애니메이션 유형: 걷기/달리기 사이클
        - 미리보기 URL: https://example.com/preview/anim123.gif
        - 다운로드 URL: https://example.com/download/anim123.zip
        
        애니메이션이 성공적으로 생성되었습니다. 위 URL에서 확인하고 다운로드할 수 있습니다.
        """
    else:
        work_results = "지원되지 않는 리소스 유형입니다."
    
    return {
        **state,
        "work_results": work_results,
        "next": "answer_step"
    }

def generate_answer(state: AgentState) -> AgentState:
    """답변 생성 단계: 최종 답변 작성"""
    llm = create_ollama_llm()
    
    if state.get("is_game_resource_request", False) and state.get("work_results"):
        prompt = PromptTemplate.from_template(
            """게임 리소스 제작 요청에 대한 최종 답변을 생성하세요:
            
            요청 내용: {question}
            요청 유형: {resource_type}
            조사 결과: {research_results}
            작업 결과: {work_results}
            
            사용자가 이해하기 쉽게 리소스 제작 과정과 결과를 설명하는 답변을 작성하세요:"""
        )
        
        resource_type = "3D 모델" if state["resource_type"] == "3d_model" else "애니메이션"
        answer = llm.invoke(
            prompt.format(
                question=state["question"],
                resource_type=resource_type,
                research_results=state["research_results"],
                work_results=state["work_results"]
            )
        )
    else:
        prompt = PromptTemplate.from_template(
            """질문에 대한 최종 답변을 생성하세요:
            
            질문: {question}
            지금까지 사고: {thoughts}
            조사 결과: {research_results}
            
            명확하고 구조화된 최종 답변:"""
        )
        
        answer = llm.invoke(
            prompt.format(
                question=state["question"],
                thoughts="\n".join(state["thoughts"]),
                research_results=state["research_results"]
            )
        )
    
    return {
        **state,
        "answer": answer,
        "next": END
    }

def router(state: AgentState) -> Union[Literal["think", "research_step", "answer_step", "work_step", "reject_request"], Literal[END]]:
    """다음 단계 결정"""
    return state["next"]

def build_agent_graph():
    """에이전트 그래프 구성"""
    workflow = StateGraph(AgentState)
    
    workflow.add_node("check_game_resource", check_game_resource_request)
    workflow.add_node("reject_request", reject_request)
    workflow.add_node("think", think)
    workflow.add_node("research_step", research)
    workflow.add_node("work_step", work_step)
    workflow.add_node("answer_step", generate_answer)
    
    workflow.set_entry_point("check_game_resource")
    
    workflow.add_conditional_edges("check_game_resource", router, {
        "think": "think",
        "reject_request": "reject_request"
    })
    
    workflow.add_conditional_edges("reject_request", router, {
        END: END
    })
    
    workflow.add_conditional_edges("think", router, {
        "research_step": "research_step",
        "answer_step": "answer_step"
    })
    
    workflow.add_conditional_edges("research_step", router, {
        "work_step": "work_step",
        "answer_step": "answer_step"
    })
    
    workflow.add_conditional_edges("work_step", router, {
        "answer_step": "answer_step"
    })
    
    workflow.add_conditional_edges("answer_step", router, {
        END: END
    })
    
    return workflow.compile()

def answer_with_agent(question: str, model_name=DEFAULT_MODEL):
    """LangGraph 에이전트를 사용하여 질문에 답변"""
    agent = build_agent_graph()
    
    initial_state = {
        "question": question,
        "thoughts": [],
        "research_results": "",
        "answer": "",
        "is_game_resource_request": False,
        "resource_type": None,
        "resource_details": {},
        "work_results": None,
        "next": "check_game_resource"
    }
    
    result = agent.invoke(initial_state)
    return result

def streaming_agent_execution(question: str, model_name=DEFAULT_MODEL):
    """에이전트 실행 과정을 스트리밍 방식으로 출력"""
    print("=== 에이전트 실행 시작 ===\n")
    
    print(f"📝 질문: {question}\n")
    
    agent = build_agent_graph()
    
    initial_state = {
        "question": question,
        "thoughts": [],
        "research_results": "",
        "answer": "",
        "is_game_resource_request": False,
        "resource_type": None,
        "resource_details": {},
        "work_results": None,
        "next": "check_game_resource"
    }
    
    for event in agent.stream(initial_state):
        node = event.get("node")
        if node:
            state = event["state"]
            
            if node == "check_game_resource":
                is_valid = state.get("is_game_resource_request", False) and state.get("resource_type") in ["3d_model", "animation"]
                print("\n🔍 요청 분석 결과:")
                print(f"게임 리소스 요청: {'예' if state.get('is_game_resource_request', False) else '아니오'}")
                if state.get('is_game_resource_request', False):
                    print(f"리소스 유형: {state.get('resource_type', '없음')}")
                    print(f"유효한 요청: {'예' if is_valid else '아니오'}")
            
            elif node == "reject_request":
                print("\n❌ 요청 거부:")
                print(state["answer"])
            
            elif node == "think" and state.get("thoughts"):
                print("\n🧠 사고 결과:")
                print(state["thoughts"][-1])
                print("\n🔍 조사 단계 시작...")
            
            elif node == "research_step" and state.get("research_results"):
                print("\n🔍 조사 결과:")
                print(state["research_results"])
                
                if state.get("is_game_resource_request", False):
                    print("\n🔨 리소스 생성 작업 시작...")
                else:
                    print("\n✍️ 답변 생성 시작...")
            
            elif node == "work_step" and state.get("work_results"):
                print("\n🔨 리소스 생성 결과:")
                print(state["work_results"])
                print("\n✍️ 답변 생성 시작...")
            
            elif node == "answer_step" and state.get("answer"):
                print("\n✅ 최종 답변:")
                print(state["answer"])
    
    print("\n=== 에이전트 실행 완료 ===")

def generate_with_gemma3(prompt, model=DEFAULT_MODEL, stream=False):
    """
    Gemma 모델을 사용하여 텍스트 생성
    
    Args:
        prompt (str): 모델에 전송할 프롬프트 텍스트
        model (str): 사용할 모델 이름 (기본값: gemma3:4b)
        stream (bool): 스트리밍 응답 여부
        
    Returns:
        dict: 모델의 응답 결과
    """
    try:
        if stream:
            result = answer_with_agent(prompt, model_name=model)
            return {
                "response": result["answer"],
                "done": True
            }
        else:
            result = answer_with_agent(prompt, model_name=model)
            return {
                "response": result["answer"],
                "done": True
            }
    except Exception as e:
        return {"error": f"생성 중 오류 발생: {str(e)}"}

if __name__ == "__main__":
    print("=== LangGraph로 Ollama 에이전트 사용하기 ===\n")
    
    question1 = "Python에서 리스트와 딕셔너너리의 차이를 설명해주세요."
    print(f"질문: {question1}")
    print("\n--- 에이전트 답변 ---")
    result = answer_with_agent(question1)
    print(f"최종 답변: {result['answer']}")
    
    print("\n\n=== 스트리밍 방식으로 에이전트 실행 ===")
    question2 = "인공지능의 미래에 대해 3가지 관점에서 설명해주세요."
    streaming_agent_execution(question2)