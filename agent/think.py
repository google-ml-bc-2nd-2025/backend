from agent.state import AgentState, PromptState
from agent.llm import create_ollama_llm
from langchain_core.prompts import PromptTemplate

def think(state: AgentState) -> AgentState:
    """사고 단계: 질문을 분석하고 접근 방법 결정"""
    llm = create_ollama_llm()
    prompt = PromptTemplate.from_template(
        """질문을 분석하고 게임 리소스 제작에 대한 사고 과정을 설명하세요:
        
        질문: {question}
        
        사고 과정:"""
    )
    
    thoughts = llm.invoke(prompt.format(question=state["question"]))
    
    return {
        **state,
        "thoughts": state.get("thoughts", []) + [thoughts],
        "next": "research_step"
    }

def check_prompt(prompt: str) -> PromptState:
    """
    프롬프트의 유효성을 검사합니다.
    
    Args:
        prompt (str): 검사할 프롬프트
        
    Returns:
        PromptState: 검사 결과 상태
    """
    state = PromptState()
    state.prompt = prompt
    
    # 1. 길이 검사
    if not prompt or len(prompt.strip()) < 5:
        state.is_valid = False
        state.error_message = "프롬프트가 너무 짧습니다. 더 자세한 설명을 입력해주세요."
        return state
        
    # 2. 특수문자 검사
    if any(char in prompt for char in ['@', '#', '$', '%', '^', '&', '*']):
        state.is_valid = False
        state.error_message = "프롬프트에 특수문자가 포함되어 있습니다."
        return state
        
    # 3. 부적절한 내용 검사
    if any(word in prompt.lower() for word in ['hack', 'attack', 'virus']):
        state.is_valid = False
        state.error_message = "부적절한 내용이 포함되어 있습니다."
        return state
        
    state.is_valid = True
    return state