"""
에이전트 컨트롤러 모듈
"""

from typing import Dict, Any, List
from .base import BaseAgent, Message
from src.utils.logger import get_agent_logger, get_system_logger
import logging

logger = logging.getLogger(__name__)

class AgentController(BaseAgent):
    def __init__(self, redis_client):
        """에이전트 컨트롤러 초기화"""
        super().__init__("controller", redis_client)
        self.agents = {}
        logger.info("AgentController 초기화 완료")
        
    async def process_message(self, message: Message):
        """메시지 처리"""
        if message.intent == "start_task":
            await self._handle_start_task(message)
        elif message.intent == "execution_error":
            await self._handle_error(message)
            
    async def _handle_start_task(self, message: Message):
        """태스크 시작 처리"""
        try:
            content = message.content
            task_id = content.get("task_id")
            prompt = content.get("prompt")
            
            if not task_id or not prompt:
                raise ValueError("필수 파라미터 누락")
                
            logger.info(f"태스크 시작: task_id={task_id}")
            
            # PromptAnalyzer에게 분석 요청
            await self.send_message(
                "prompt_analyzer",
                "analyze_prompt",
                {
                    "task_id": task_id,
                    "prompt": prompt
                }
            )
            
        except Exception as e:
            logger.error(f"태스크 시작 실패: {e}", exc_info=True)
            await self._handle_error(Message(
                sender="controller",
                intent="execution_error",
                content={
                    "task_id": task_id,
                    "error": str(e)
                }
            ))
            
    async def _handle_error(self, message: Message):
        """오류 처리"""
        content = message.content
        task_id = content.get("task_id")
        error = content.get("error")
        
        logger.error(f"태스크 오류: task_id={task_id}, error={error}")
        
        # 클라이언트에게 오류 전송
        await self.send_message(
            "client",
            "task_error",
            {
                "task_id": task_id,
                "error": error
            }
        ) 