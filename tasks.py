"""
작업 처리 모듈
"""

import time
import logging
from typing import Dict, Any
from generate import refine_prompt
from mdm import generate_animation

logger = logging.getLogger(__name__)

async def process_prompt(prompt: str) -> Dict[str, Any]:
    """
    프롬프트를 처리하는 함수
    
    Args:
        prompt: 사용자 입력 프롬프트
        
    Returns:
        작업 결과 딕셔너리
    """
    start_time = time.time()
    
    try:
        # 프롬프트 정제
        text_refinement_start = time.time()
        logger.info("Starting text refinement")
        
        refined_result = refine_prompt(prompt)
        if refined_result['status'] != 'success':
            raise Exception(f"텍스트 정제 실패: {refined_result.get('error')}")
        
        refined_text = refined_result['refined_text']
        text_refinement_duration = time.time() - text_refinement_start
        
        # AI 모델 서버로 프롬프트 전달
        motion_generation_start = time.time()
        logger.info("Starting motion generation")
        
        motion_result = await generate_animation(refined_text)
        if motion_result['status'] != 'success':
            raise Exception(f"모션 생성 요청 실패: {motion_result.get('error')}")
        
        motion_generation_duration = time.time() - motion_generation_start
        
        return {
            "status": "completed",
            "text_result": refined_text,
            "timing": {
                "text_refinement_duration": text_refinement_duration,
                "motion_generation_duration": motion_generation_duration,
                "total_duration": time.time() - start_time
            }
        }
        
    except Exception as e:
        logger.error(f"프롬프트 처리 중 오류 발생: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }
