from typing import Dict, List, Optional, TypedDict

class AgentState(TypedDict):
    """에이전트 상태 정의"""
    question: str
    thoughts: List[str]
    research_results: str
    answer: str
    is_game_resource_request: bool
    resource_type: Optional[str]
    resource_details: Dict[str, str]
    work_results: Optional[str]
    next: str

class PromptState:
    """프롬프트 검사 상태 관리"""
    def __init__(self):
        self.prompt = None
        self.is_valid = False
        self.error_message = None