import json
from agent.state import AgentState
from agent.llm import create_ollama_llm
from langchain_core.prompts import PromptTemplate

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