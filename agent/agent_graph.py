from typing import Union, Literal
from langgraph.graph import StateGraph, END

from agent.state import AgentState
from agent.check_game_resource import check_game_resource_request, reject_request
from agent.think import think
from agent.research import research
from agent.work import work_step
from agent.answer import generate_answer

def router(state: AgentState) -> Union[Literal["think", "research_step", "answer_step", "work_step", "reject_request"], Literal[END]]:
    """다음 단계 결정"""
    next_step = state["next"]
    # END 문자열을 실제 END 상수로 변환
    if next_step == "END":
        return END
    return next_step

def build_agent_graph():
    """에이전트 그래프 구성"""
    workflow = StateGraph(AgentState)
    
    # 노드 추가
    workflow.add_node("check_game_resource", check_game_resource_request)
    workflow.add_node("reject_request", reject_request)
    workflow.add_node("think", think)
    workflow.add_node("research_step", research)
    workflow.add_node("work_step", work_step)
    workflow.add_node("answer_step", generate_answer)
    
    # 시작 노드 설정
    workflow.set_entry_point("check_game_resource")
    
    # 엣지 연결
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
    
    # 그래프 컴파일
    return workflow.compile()