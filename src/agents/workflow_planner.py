"""
워크플로우 플래너 모듈
분석 결과를 받아 작업 흐름을 계획하고 관리합니다.
"""

from typing import Dict, Any, List
from .base import BaseAgent, Message
import logging
from enum import Enum

logger = logging.getLogger(__name__)

class StepPriority(Enum):
    HIGH = 3
    MEDIUM = 2
    LOW = 1

class WorkflowPlanner(BaseAgent):
    def __init__(self, redis_client):
        """워크플로우 플래너 초기화"""
        super().__init__("workflow_planner", redis_client)
        self.resource_pool = {
            "cpu": 4,  # 가용 CPU 코어 수
            "gpu": 1,  # 가용 GPU 수
            "memory": 16  # 가용 메모리(GB)
        }
        logger.info("WorkflowPlanner 초기화 완료")
        
    async def process_message(self, message: Message):
        """분석 결과를 받아 워크플로우를 계획합니다."""
        if message.intent != "plan_workflow":
            logger.warning(f"알 수 없는 메시지 intent: {message.intent}")
            return
            
        try:
            analysis_result = message.content.get("analysis_result")
            task_id = message.content.get("task_id")
            original_prompt = message.content.get("original_prompt")
            
            logger.info(f"워크플로우 계획 시작: task_id={task_id}")
            
            # 워크플로우 계획 생성
            workflow = self._create_workflow(analysis_result)
            
            # 리소스 할당 및 우선순위 설정
            workflow = self._optimize_workflow(workflow)
            
            # TaskExecutor에게 실행 계획 전달
            await self.send_message(
                "task_executor",
                "execute_workflow",
                {
                    "workflow": workflow,
                    "task_id": task_id,
                    "original_prompt": original_prompt
                }
            )
            
            logger.info(f"워크플로우 계획 완료: task_id={task_id}")
            
        except Exception as e:
            logger.error(f"워크플로우 계획 실패: {e}", exc_info=True)
            await self._handle_error(task_id, str(e))
            
    def _create_workflow(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """분석 결과를 기반으로 워크플로우를 생성합니다."""
        if not analysis_result or "translation" not in analysis_result or "motion" not in analysis_result:
            raise ValueError("잘못된 분석 결과 형식")
            
        # 기본 워크플로우 생성
        workflow = {
            "steps": [],
            "dependencies": {},
            "resources": {},
            "metadata": {
                "emotion": analysis_result["translation"],
                "motion_type": analysis_result["motion"]
            }
        }
        
        # 동작 유형에 따른 단계 구성
        motion_type = analysis_result["motion"].lower()
        if motion_type in ["running", "walking"]:
            workflow["steps"].extend([
                {
                    "step_id": "prepare_motion",
                    "action": "prepare_motion_data",
                    "priority": StepPriority.HIGH,
                    "params": {
                        "emotion": analysis_result["translation"],
                        "motion_type": motion_type
                    }
                },
                {
                    "step_id": "generate_animation",
                    "action": "create_animation",
                    "priority": StepPriority.HIGH,
                    "params": {
                        "motion_data": "{{prepare_motion.output}}",
                        "style": "default"
                    }
                }
            ])
        else:
            workflow["steps"].extend([
                {
                    "step_id": "prepare_motion",
                    "action": "prepare_motion_data",
                    "priority": StepPriority.MEDIUM,
                    "params": {
                        "emotion": analysis_result["translation"],
                        "motion_type": motion_type
                    }
                },
                {
                    "step_id": "generate_animation",
                    "action": "create_animation",
                    "priority": StepPriority.MEDIUM,
                    "params": {
                        "motion_data": "{{prepare_motion.output}}",
                        "style": "default"
                    }
                }
            ])
            
        # 후처리 단계 추가
        workflow["steps"].append({
            "step_id": "post_process",
            "action": "apply_post_processing",
            "priority": StepPriority.LOW,
            "params": {
                "animation": "{{generate_animation.output}}",
                "effects": []
            }
        })
        
        # 의존성 설정
        workflow["dependencies"] = {
            "generate_animation": ["prepare_motion"],
            "post_process": ["generate_animation"]
        }
        
        return workflow
        
    def _optimize_workflow(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """워크플로우 최적화"""
        # 리소스 할당
        for step in workflow["steps"]:
            step_id = step["step_id"]
            priority = step["priority"]
            
            # 우선순위에 따른 리소스 할당
            if priority == StepPriority.HIGH:
                workflow["resources"][step_id] = {
                    "cpu": 2,
                    "gpu": 1,
                    "memory": 8
                }
            elif priority == StepPriority.MEDIUM:
                workflow["resources"][step_id] = {
                    "cpu": 1,
                    "gpu": 0.5,
                    "memory": 4
                }
            else:
                workflow["resources"][step_id] = {
                    "cpu": 1,
                    "gpu": 0,
                    "memory": 2
                }
                
        return workflow
        
    async def _handle_error(self, task_id: str, error: str):
        """오류 처리"""
        logger.error(f"작업 오류: task_id={task_id}, error={error}")
        await self.send_message(
            "controller",
            "execution_error",
            {
                "task_id": task_id,
                "error": error
            }
        ) 