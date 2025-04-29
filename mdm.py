import logging
import requests
import os
from typing import Dict
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

logger = logging.getLogger(__name__)

# MDM 서버 설정
MDM_SERVER_URL = os.getenv("MDM_SERVER_URL", "http://47.186.55.156:57179")
TIMEOUT = 60.0  # 요청 타임아웃 (초)

async def generate_animation(prompt: str) -> Dict:
    """
    프롬프트를 AI 모델 서버로 전달합니다.
    """
    try:
        logger.info(f"[DEBUG] 모션 생성 요청: prompt={prompt}")
        response = requests.post(
            f'{MDM_SERVER_URL}/predict',
            json={'prompt': prompt, 'num_repetitions': 1},
            timeout=TIMEOUT
        )
        logger.info(f"[DEBUG] 모션 생성 응답: status_code={response.status_code}")
        if response.status_code == 200:
            return {
                'status': 'success',
                'message': '모션 생성 요청이 성공적으로 전송되었습니다'
            }
        else:
            return {
                'status': 'failed',
                'error': f'모션 생성 요청 실패: {response.status_code}'
            }
    except Exception as e:
        logger.error(f"[DEBUG] 모션 생성 오류: {str(e)}")
        return {
            'status': 'failed',
            'error': str(e)
        }