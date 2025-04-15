"""
태스크 실행기 모듈
워크플로우 플래너로부터 받은 작업을 실제로 실행합니다.
"""

import os
import numpy as np
from typing import Dict, Any, Optional, Union
from pathlib import Path
from .base import BaseAgent, Message
import logging
import asyncio
import json
from redis import Redis

logger = logging.getLogger(__name__)

class TaskExecutor:
    """작업 실행기"""
    def __init__(self, redis_client: Redis, output_dir: Union[str, Path]):
        """초기화"""
        self.redis_client = redis_client
        self.output_dir = Path(output_dir)
        self.active_tasks = {}
        self.resource_usage = {"cpu": 0.0, "gpu": 0.0}
        
        # 출력 디렉토리 생성
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    async def process_message(self, message: Message) -> None:
        """메시지 처리"""
        try:
            if message.intent == "execute_workflow":
                await self._handle_execute_workflow(message)
            elif message.intent == "cancel_workflow":
                await self._handle_cancel_workflow(message)
        except Exception as e:
            logger.error(f"메시지 처리 중 오류: {str(e)}")
        if message.intent == "execute_workflow":
                task_id = message.content.get("task_id")
                if task_id:
                    await self._update_status(task_id, "failed", 0.0)
                    error_message = Message(
                        sender="task_executor",
                        intent="execution_error",
                        content={
                            "task_id": task_id,
                            "error": str(e)
                        }
                    )
                    await self.redis_client.publish("task_status", error_message.to_json())

    async def _handle_execute_workflow(self, message: Message) -> None:
        """워크플로우 실행 처리"""
        task_id = message.content["task_id"]
        try:
            workflow = message.content["workflow"]
            
            # 리소스 확인
            if not await self._check_resources(workflow["resources"]):
                error_message = Message(
                    sender="task_executor",
                    intent="execution_error",
                    content={
                        "task_id": task_id,
                        "error": "리소스 부족"
                    }
                )
                await self.redis_client.publish("task_status", error_message.to_json())
                return

            # 작업 상태 초기화
            self.active_tasks[task_id] = {
                "status": "running",
                "progress": 0.0,
                "cancelled": False
            }

            # 상태 업데이트
            await self._update_status(task_id, "running", 0.0)

            # 워크플로우 실행
            result = None
            total_steps = len(workflow["steps"])
            for i, step in enumerate(workflow["steps"]):
                if self.active_tasks[task_id]["cancelled"]:
                    await self._update_status(task_id, "cancelled", (i * 100.0) / total_steps)
                    return

                step_result = await self._execute_step(step, workflow, task_id)
                if i == 0:  # prepare_motion_data 단계
                    result = step_result
                elif i == 1:  # create_animation 단계
                    result = step_result
                elif i == 2:  # apply_post_processing 단계
                    result.update(step_result)
                await self._update_status(task_id, "running", ((i + 1) * 100.0) / total_steps)

            # 결과 저장
            if result:
                await self._save_result(task_id, result)
                await self._update_status(task_id, "completed", 100.0)
            else:
                await self._update_status(task_id, "failed", 0.0)

        except asyncio.CancelledError:
            await self._update_status(task_id, "cancelled", 0.0)
            error_message = Message(
                sender="task_executor",
                intent="execution_error",
                content={
                    "task_id": task_id,
                    "error": "작업이 취소되었습니다"
                }
            )
            await self.redis_client.publish("task_status", error_message.to_json())
        except Exception as e:
            logger.error(f"워크플로우 실행 중 오류: {str(e)}")
            await self._update_status(task_id, "failed", 0.0)
            error_message = Message(
                sender="task_executor",
                intent="execution_error",
                content={
                    "task_id": task_id,
                    "error": str(e)
                }
            )
            await self.redis_client.publish("task_status", error_message.to_json())

    async def _handle_cancel_workflow(self, message: Message) -> None:
        """워크플로우 취소 처리"""
        task_id = message.content["task_id"]
        if task_id in self.active_tasks:
            self.active_tasks[task_id]["cancelled"] = True
            await self._update_status(task_id, "cancelled", 0.0)
            logger.info(f"작업 취소 요청됨: {task_id}")
        else:
            logger.warning(f"취소할 작업을 찾을 수 없습니다: {task_id}")

    async def _execute_step(self, step: Dict[str, Any], workflow: Dict[str, Any], task_id: str) -> Dict[str, Any]:
        """워크플로우 단계 실행"""
        try:
            # 취소 확인
            if task_id in self.active_tasks and self.active_tasks[task_id]["cancelled"]:
                raise asyncio.CancelledError()

            # 단계 정보 추출
            step_id = step.get("step_id")
            action = step.get("action")
            params = step.get("params", {})

            if action == "prepare_motion_data":
                return await self._prepare_motion_data(params)
            elif action == "create_animation":
                return await self._create_motion(params)
            elif action == "apply_post_processing":
                return await self._apply_effect(params)
            else:
                raise ValueError(f"알 수 없는 액션: {action}")
                
        except asyncio.CancelledError:
            logger.info(f"작업 취소됨: {task_id}")
            raise
        except Exception as e:
            logger.error(f"단계 실행 중 오류: {str(e)}")
            raise

    async def _prepare_motion_data(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """모션 데이터 준비"""
        try:
            # 입력 파일 경로 확인
            input_file = params.get("input_file")
            if not input_file:
                raise ValueError("입력 파일 경로가 지정되지 않았습니다")
            
            if not os.path.exists(input_file):
                raise FileNotFoundError(f"입력 파일이 존재하지 않습니다: {input_file}")
            
            # SMPL 데이터 로드
            smpl_data = np.load(input_file, allow_pickle=True).item()
            
            # 모션 데이터 준비
            motion_data = {
                "poses": smpl_data["poses"],
                "fps": smpl_data["fps"]
            }
            
            return motion_data
        
        except Exception as e:
            logger.error(f"모션 데이터 준비 실패: {str(e)}")
            raise

    async def _create_motion(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """모션 생성"""
        # 임시 구현: 더미 데이터 반환
        return {
            "poses": np.zeros((60, 72)),  # 60 프레임, 72 차원
            "fps": 30.71428623734689
        }

    async def _apply_effect(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """효과 적용"""
        # 임시 구현: 입력을 그대로 반환
        return params

    async def _save_result(self, task_id: str, result: Dict[str, Any]) -> None:
        """결과 저장"""
        try:
            output_dir = self.output_dir / task_id
            output_dir.mkdir(parents=True, exist_ok=True)

            # 애니메이션 데이터 저장
            animation_file = output_dir / "animation.npy"
            animation_data = {
                "poses": result["poses"],
                "fps": result["fps"]
            }
            np.save(animation_file, animation_data)

            # 메타데이터 저장
            metadata = {
                "fps": result["fps"],
                "duration": len(result["poses"]) / result["fps"],
                "effects": result.get("effects", [])
            }
            metadata_file = output_dir / "metadata.json"
            with open(metadata_file, "w") as f:
                json.dump(metadata, f, indent=2)

            logger.info(f"결과 저장 완료: {task_id}")
        except Exception as e:
            logger.error(f"결과 저장 중 오류: {str(e)}")
            raise
        
    async def _update_status(self, task_id: str, status: str, progress: float) -> None:
        """작업 상태 업데이트"""
        try:
            if task_id in self.active_tasks:
                self.active_tasks[task_id]["status"] = status
                self.active_tasks[task_id]["progress"] = progress
                
                status_message = Message(
                    sender="task_executor",
                    intent="status_update",
                    content={
                        "task_id": task_id,
                        "status": status,
                        "progress": progress
                    }
                )
                await self.redis_client.publish("task_status", status_message.to_json())
                logger.info(f"상태 업데이트: task_id={task_id}, status={status}, progress={progress}")
            else:
                logger.warning(f"작업을 찾을 수 없습니다: {task_id}")
        except Exception as e:
            logger.error(f"상태 업데이트 중 오류: {str(e)}")
        
    async def _check_resources(self, required_resources: Dict[str, Dict[str, float]]) -> bool:
        """리소스 확인"""
        try:
            total_cpu = 0.0
            total_gpu = 0.0
            
            for action, resources in required_resources.items():
                total_cpu += resources.get("cpu", 0.0)
                total_gpu += resources.get("gpu", 0.0)
                
            available_cpu = 1.0 - self.resource_usage.get("cpu", 0.0)
            available_gpu = 1.0 - self.resource_usage.get("gpu", 0.0)
            
            return total_cpu <= available_cpu and total_gpu <= available_gpu
        except Exception as e:
            logger.error(f"리소스 확인 중 오류: {str(e)}")
            return False 