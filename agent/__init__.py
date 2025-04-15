from agent.agent_graph import build_agent_graph
from agent.state import AgentState
from agent.llm import create_ollama_llm, DEFAULT_MODEL

def answer_with_agent(question: str, model_name=DEFAULT_MODEL):
    """LangGraph 에이전트를 사용하여 질문에 답변"""
    agent = build_agent_graph()
    
    # 에이전트 실행
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
    
    # 그래프 실행 및 결과 반환
    result = agent.invoke(initial_state)
    return result

def streaming_agent_execution(question: str, model_name=DEFAULT_MODEL):
    """에이전트 실행 과정을 스트리밍 방식으로 출력"""
    print("=== 에이전트 실행 시작 ===\n")
    
    print(f"📝 질문: {question}\n")
    
    agent = build_agent_graph()
    
    # 에이전트 실행 및 각 단계 출력
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