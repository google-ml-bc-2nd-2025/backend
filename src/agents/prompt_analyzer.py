"""
프롬프트 분석기 모듈
사용자의 프롬프트를 분석하여 감정과 동작을 추출합니다.
"""

from typing import Dict, Any
from .base import BaseAgent, Message
import logging

logger = logging.getLogger(__name__)

class PromptAnalyzer(BaseAgent):
    def __init__(self, redis_client):
        """프롬프트 분석기 초기화"""
        super().__init__("prompt_analyzer", redis_client)
        logger.info("PromptAnalyzer 초기화 완료")
        
    async def process_message(self, message: Message):
        """메시지 처리"""
        if message.intent == "analyze_prompt":
            await self._handle_analyze_prompt(message)
            
    async def _handle_analyze_prompt(self, message: Message):
        """프롬프트 분석 처리"""
        try:
            content = message.content
            task_id = content.get("task_id")
            prompt = content.get("prompt")
            
            if not task_id or not prompt:
                raise ValueError("필수 파라미터 누락")
                
            logger.info(f"프롬프트 분석 시작: task_id={task_id}")
            
            # 프롬프트 분석
            analysis_result = self._analyze_prompt(prompt)
            
            # WorkflowPlanner에게 결과 전달
            await self.send_message(
                "workflow_planner",
                "plan_workflow",
                {
                    "analysis_result": analysis_result,
                    "task_id": task_id,
                    "original_prompt": prompt
                }
            )
            
            logger.info(f"프롬프트 분석 완료: task_id={task_id}")
            
        except Exception as e:
            logger.error(f"프롬프트 분석 실패: {e}", exc_info=True)
            await self._handle_error(task_id, str(e))
            
    def _analyze_prompt(self, prompt: str) -> Dict[str, Any]:
        """프롬프트 분석 로직"""
        # TODO: 실제 분석 로직 구현
        # 임시로 하드코딩된 결과 반환
        return {
            "translation": "HAPPILY",
            "motion": "RUNNING"
        }
        
    async def _handle_error(self, task_id: str, error: str):
        """오류 처리"""
        logger.error(f"분석 오류: task_id={task_id}, error={error}")
        await self.send_message(
            "controller",
            "execution_error",
            {
                "task_id": task_id,
                "error": error
            }
        ) 