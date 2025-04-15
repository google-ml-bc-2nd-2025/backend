import json
from agent.state import AgentState
from agent.llm import create_ollama_llm
from langchain_core.prompts import PromptTemplate

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
        "next": "END"
    }