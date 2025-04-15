from agent.state import AgentState
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