"""
텍스트 생성 및 정제를 위한 Google API 연동 모듈
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging
import os
from dotenv import load_dotenv
import google.generativeai as genai
from mdm import generate_animation

# 환경 변수 로드
load_dotenv()

# Google API 키 설정
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY가 설정되지 않았습니다. .env 파일을 확인해주세요.")

# Google AI 초기화
genai.configure(api_key=GOOGLE_API_KEY)

# 라우터 설정
router = APIRouter(prefix="/api", tags=["generate"])
logger = logging.getLogger(__name__)

def refine_prompt(prompt: str) -> Dict[str, Any]:
    """
    사용자 프롬프트를 모션 생성에 적합한 형태로 정제

    Args:
        prompt (str): 사용자 입력 프롬프트

    Returns:
        Dict[str, Any]: {
            'status': 'success' | 'error',
            'refined_text': str,  # 정제된 프롬프트
            'error': str,  # 에러 발생 시 에러 메시지
        }
    """
    try:
        # Gemini 모델 설정
        model = genai.GenerativeModel('gemini-1.5-pro')
        
        # 프롬프트 템플릿
        system_prompt = """
        당신은 텍스트를 3D 모션 생성에 적합한 형태로 변환하는 전문가입니다.
        입력된 텍스트를 다음 기준에 맞춰 정제해주세요:

        1. 동작의 속도, 강도, 감정을 명확하게 표현
        2. 신체의 각 부위(팔, 다리, 몸통 등)의 움직임을 구체적으로 기술
        3. 동작의 시작과 끝을 명확하게 정의
        4. 불필요한 수식어나 모호한 표현 제거

        출력 형식:
        - 한 문장으로 된 명확한 동작 설명
        - 영어로 변환
        """
        
        # 프롬프트 전송
        response = model.generate_content([
            system_prompt,
            f"입력 텍스트: {prompt}\n변환된 텍스트:"
        ])
        
        # 응답 처리
        if response.text:
            return {
                'status': 'success',
                'refined_text': response.text.strip()
            }
        else:
            raise ValueError("API 응답이 비어있습니다.")
            
    except Exception as e:
        logger.error(f"프롬프트 정제 중 오류 발생: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }

def generate_with_retry(prompt: str, max_retries: int = 3) -> Dict[str, Any]:
    """
    재시도 로직이 포함된 텍스트 생성 함수

    Args:
        prompt (str): 사용자 입력 프롬프트
        max_retries (int): 최대 재시도 횟수

    Returns:
        Dict[str, Any]: 정제된 텍스트 또는 에러 정보
    """
    for attempt in range(max_retries):
        result = refine_prompt(prompt)
        if result['status'] == 'success':
            return result
        logger.warning(f"프롬프트 정제 재시도 {attempt + 1}/{max_retries}")
    
    return {
        'status': 'error',
        'error': f"최대 재시도 횟수({max_retries})를 초과했습니다."
    }
