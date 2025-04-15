import json
import re
from agent.state import AgentState
from agent.llm import create_ollama_llm
from langchain_core.prompts import PromptTemplate

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
        "next": "END"
    }