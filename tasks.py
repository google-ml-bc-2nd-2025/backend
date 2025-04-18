"""
Celery 작업 정의 모듈
"""

from celery import Task
from celery_app import app
import time
from datetime import datetime, timezone
import logging
from typing import Optional, Dict, Any
from generate import generate_with_retry
from mdm import generate_animation

logger = logging.getLogger(__name__)

class TaskStatus:
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class ProcessingStep:
    TEXT_REFINEMENT = "text_refinement"
    MOTION_GENERATION = "motion_generation"

class ErrorCodes:
    TEXT_REFINEMENT_FAILED = "TEXT_REFINEMENT_FAILED"
    MOTION_GENERATION_FAILED = "MOTION_GENERATION_FAILED"
    INVALID_PROMPT = "INVALID_PROMPT"
    SYSTEM_ERROR = "SYSTEM_ERROR"

class AnimationTask(Task):
    """애니메이션 생성 작업 기본 클래스"""
    
    def __init__(self):
        self.current_step = None
    
    def on_success(self, retval, task_id, args, kwargs):
        """작업 성공 시 호출"""
        logger.info(f"Task {task_id} completed successfully")
        self.update_task_timing(task_id, "completed_at")
        
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """작업 실패 시 호출"""
        logger.error(f"Task {task_id} failed: {exc}")
        self.update_task_timing(task_id, "completed_at")
        
    def update_task_timing(self, task_id: str, timing_key: str):
        """작업 타이밍 정보 업데이트"""
        app.backend.store_result(
            task_id,
            {
                timing_key: datetime.now(timezone.utc).isoformat()
            },
            "SUCCESS"
        )

@app.task(bind=True, base=AnimationTask)
def generate_text_async(self, prompt: str, model: str = "gemini-1.5-pro", 
                       stream: bool = False, service: str = "google") -> Dict[str, Any]:
    """
    비동기 텍스트 생성 작업
    
    Args:
        prompt: 사용자 입력 프롬프트
        model: 사용할 모델 이름
        stream: 스트리밍 여부
        service: 사용할 서비스
        
    Returns:
        작업 결과 딕셔너리
    """
    task_id = self.request.id
    start_time = time.time()
    
    try:
        # 작업 시작 시간 기록
        self.update_task_timing(task_id, "started_at")
        
        # 텍스트 정제 시작
        self.current_step = ProcessingStep.TEXT_REFINEMENT
        text_refinement_start = time.time()
        logger.info(f"Starting text refinement for task {task_id}")
        
        # Google API를 사용한 텍스트 정제
        refined_result = generate_with_retry(prompt)
        if refined_result['status'] != 'success':
            raise Exception(f"텍스트 정제 실패: {refined_result.get('error')}")
        
        refined_text = refined_result['refined_text']
        text_refinement_duration = time.time() - text_refinement_start
        
        # 모션 생성 시작
        self.current_step = ProcessingStep.MOTION_GENERATION
        motion_generation_start = time.time()
        logger.info(f"Starting motion generation for task {task_id}")
        
        # MDM 모델 호출
        motion_result = generate_animation(refined_text)
        if motion_result['status'] != 'success':
            raise Exception(f"모션 생성 실패: {motion_result.get('error')}")
        
        motion_data = motion_result['motion_data']
        motion_metadata = motion_result.get('metadata', {})
        motion_generation_duration = time.time() - motion_generation_start
        
        return {
            "status": "completed",
            "text_result": refined_text,
            "animation_result": {
                "smpl_data": motion_data,
                "metadata": motion_metadata,
                "timing": {
                    "text_refinement_duration": text_refinement_duration,
                    "motion_generation_duration": motion_generation_duration,
                    "total_duration": time.time() - start_time
                }
            }
        }
            
    except Exception as e:
        logger.error(f"Task {task_id} failed: {str(e)}")
        return {
            "status": "failed",
            "error": {
                "code": ErrorCodes.TEXT_REFINEMENT_FAILED if self.current_step == ProcessingStep.TEXT_REFINEMENT
                       else ErrorCodes.MOTION_GENERATION_FAILED,
                "message": "작업 처리 중 오류가 발생했습니다.",
                "details": str(e),
                "step": self.current_step
            },
            "timing": {
                "total_duration": time.time() - start_time
            }
        }
