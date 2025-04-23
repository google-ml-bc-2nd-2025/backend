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
from agent.think import check_prompt
from generate import refine_prompt
from agent.state import PromptState
import json

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
        self.update_task_timing(task_id, "completed_at", status="SUCCESS")
        
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """작업 실패 시 호출"""
        logger.error(f"Task {task_id} failed: {exc}")
        self.update_task_timing(task_id, "completed_at", status="FAILED")
        
    def update_task_timing(self, task_id: str, timing_key: str, status: str = "PENDING"):
        """작업 타이밍 정보 업데이트
        
        Args:
            task_id: 작업 ID
            timing_key: 타이밍 정보 키
            status: 작업 상태 (기본값: "PENDING")
        """
        app.backend.store_result(
            task_id,
            {
                timing_key: datetime.now(timezone.utc).isoformat()
            },
            status
        )

@app.task(bind=True, base=AnimationTask)
def generate_text_async(self, prompt: str) -> Dict[str, Any]:
    """
    비동기 텍스트 생성 작업
    
    Args:
        prompt: 사용자 입력 프롬프트
        
    Returns:
        작업 결과 딕셔너리
    """
    task_id = self.request.id
    start_time = time.time()
    
    try:
        # 작업 시작 시간 기록
        self.update_task_timing(task_id, "started_at", status="PROCESSING")
        
        # 프롬프트 검사
        prompt_state = check_prompt(prompt)
        if not prompt_state.is_valid:
            return {
                "status": "failed",
                "error": {
                    "code": "INVALID_PROMPT",
                    "message": prompt_state.error_message
                }
            }
        
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
        print(f"[DEBUG] 모션 생성 시작: task_id={task_id}")
        
        # MDM 모델 호출 (동기적으로 변환)
        import asyncio
        print(f"[DEBUG] MDM 모델 호출 전: refined_text={refined_text}")
        motion_result = asyncio.run(generate_animation(refined_text))
        print(f"[DEBUG] MDM 모델 호출 결과: {motion_result}")
        
        if motion_result['status'] != 'success':
            print(f"[DEBUG] 모션 생성 실패: {motion_result.get('error')}")
            raise Exception(f"모션 생성 실패: {motion_result.get('error')}")
        
        motion_array = motion_result['motion_data']
        motion_metadata = motion_result.get('metadata', {})
        motion_generation_duration = time.time() - motion_generation_start
        print(f"[DEBUG] 모션 데이터: shape={motion_array.shape}, dtype={motion_array.dtype}")
        print(f"[DEBUG] 모션 메타데이터: {motion_metadata}")
        
        # Redis에 모션 데이터 저장
        from mdm import MotionGenerator
        generator = MotionGenerator()
        print(f"[DEBUG] Redis 저장 전 데이터: shape={motion_array.shape}")
        data_key = generator.save_motion_data(motion_array, task_id)
        print(f"[DEBUG] Redis 저장 완료: data_key={data_key}")
        
        return {
            "status": "completed",
            "text_result": refined_text,
            "animation_result": {
                "smpl_data": {
                    "pose": motion_array.tolist(),
                    "betas": [],
                    "trans": []
                },
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
        error_code = ErrorCodes.TEXT_REFINEMENT_FAILED if self.current_step == ProcessingStep.TEXT_REFINEMENT else ErrorCodes.MOTION_GENERATION_FAILED
        error_message = str(e)
        
        return {
            "status": "failed",
            "error": {
                "code": error_code,
                "message": error_message,
                "details": str(e),
                "step": self.current_step
            },
            "timing": {
                "total_duration": time.time() - start_time
            }
        }

@app.task
def process_prompt(prompt: str) -> dict:
    """
    프롬프트를 처리하는 메인 태스크입니다.
    
    Args:
        prompt (str): 사용자 입력 프롬프트
        
    Returns:
        dict: 처리 결과
    """
    # 1. 프롬프트 검사
    prompt_state = check_prompt(prompt)
    
    if not prompt_state.is_valid:
        return {
            'status': 'error',
            'message': prompt_state.error_message
        }
    
    # 2. 프롬프트 개선
    try:
        result = refine_prompt(prompt)
        if result['status'] == 'success':
            return {
                'status': 'success',
                'refined_prompt': result['refined_text']
            }
        else:
            return {
                'status': 'error',
                'message': result.get('error', '프롬프트 처리 중 오류 발생')
            }
    except Exception as e:
        return {
            'status': 'error',
            'message': f'프롬프트 처리 중 오류 발생: {str(e)}'
        }
