"""
Motion Diffusion Model (MDM) 인터페이스
실제 모델과의 통합을 위한 인터페이스 정의
"""

import logging
import time
import requests
import os
import uuid
import json
import base64
import numpy as np
from typing import Dict, Any, Optional, Union, List
from dataclasses import dataclass
from enum import Enum
import redis
import httpx
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

logger = logging.getLogger(__name__)

# AI 모델 서버 URL
AI_MODEL_SERVER_URL = os.getenv("AI_MODEL_SERVER_URL", "http://localhost:8002")

# Redis 연결
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "redis"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    db=int(os.getenv("REDIS_DB", 0)),
    decode_responses=False
)

# MDM 서버 설정
MDM_SERVER_URL = os.getenv("MDM_SERVER_URL", "http://82.141.118.2:2001")
TIMEOUT = 60.0  # 요청 타임아웃 (초)

class MotionGenerationError(Exception):
    """모션 생성 중 발생하는 에러를 처리하기 위한 커스텀 예외"""
    def __init__(self, message: str, error_code: str, details: Optional[Dict] = None):
        super().__init__(message)
        self.error_code = error_code
        self.details = details or {}

class MotionStatus(str, Enum):
    """모션 생성 상태를 나타내는 열거형"""
    INITIALIZING = "initializing"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class MotionMetadata:
    """모션 데이터의 메타데이터"""
    prompt: str
    model_version: str
    generation_time: float
    frame_count: int
    fps: float = 30.0
    additional_info: Dict[str, Any] = None
    data_key: Optional[str] = None  # Redis에 저장된 데이터의 키

    def to_dict(self) -> Dict[str, Any]:
        """메타데이터를 딕셔너리로 변환"""
        return {
            "prompt": self.prompt,
            "model_version": self.model_version,
            "generation_time": self.generation_time,
            "frame_count": self.frame_count,
            "fps": self.fps,
            "data_key": self.data_key,
            **(self.additional_info or {})
        }

class MotionData:
    """모션 데이터를 관리하는 클래스"""
    def __init__(
        self,
        joints: np.ndarray,  # Shape: (num_frames, num_joints, 3)
        metadata: MotionMetadata
    ):
        self.joints = joints
        self.metadata = metadata
        self._validate()
    
    def _validate(self):
        """모션 데이터 유효성 검사"""
        if len(self.joints.shape) != 3:
            raise ValueError("관절 데이터는 3차원 배열이어야 합니다 (프레임, 관절, 좌표)")
        if self.joints.shape[0] != self.metadata.frame_count:
            raise ValueError("프레임 수가 메타데이터와 일치하지 않습니다")
    
    def to_smpl(self) -> bytes:
        """모션 데이터를 SMPL 형식으로 변환"""
        # TODO: 실제 SMPL 변환 로직 구현
        return json.dumps({
            "joints": self.joints.tolist(),
            "metadata": self.metadata.to_dict()
        }).encode()

class MotionGenerator:
    """모션 생성을 관리하는 메인 클래스"""
    def __init__(self, model_version: str = "test-v1"):
        self.model_version = model_version
        self.status = MotionStatus.INITIALIZING
        logger.info(f"MotionGenerator 초기화 (버전: {model_version})")
    
    def save_motion_data(self, motion_data: Union[np.ndarray, bytes], prompt: str) -> str:
        """모션 데이터를 Redis에 저장하고 키를 반환"""
        try:
            # 고유 키 생성
            data_key = f"motion:{uuid.uuid4()}"
            
            # NumPy 배열인 경우
            if isinstance(motion_data, np.ndarray):
                # NumPy 배열을 JSON 직렬화 가능한 형태로 변환
                data_dict = {
                    "type": "numpy",
                    "shape": motion_data.shape,
                    "dtype": str(motion_data.dtype),
                    "data": base64.b64encode(motion_data.tobytes()).decode('utf-8')
                }
            # 바이트 데이터인 경우
            else:
                data_dict = {
                    "type": "bytes",
                    "data": base64.b64encode(motion_data).decode('utf-8')
                }
            
            # Redis에 저장 (1시간 유효)
            redis_client.setex(
                data_key,
                3600,  # 1시간 TTL
                json.dumps(data_dict)
            )
            
            logger.info(f"모션 데이터 Redis 저장 완료: {data_key}")
            return data_key
            
        except Exception as e:
            logger.error(f"모션 데이터 Redis 저장 실패: {str(e)}")
            raise MotionGenerationError(
                message="모션 데이터 저장 중 오류 발생",
                error_code="SAVE_ERROR",
                details={"error": str(e)}
            )
    
    def load_motion_data(self, data_key: str) -> Union[np.ndarray, bytes]:
        """Redis에서 모션 데이터를 로드"""
        try:
            data_json = redis_client.get(data_key)
            if not data_json:
                raise MotionGenerationError(
                    message="모션 데이터를 찾을 수 없습니다",
                    error_code="DATA_NOT_FOUND"
                )
            
            data_dict = json.loads(data_json)
            
            if data_dict["type"] == "numpy":
                # NumPy 배열로 복원
                data_bytes = base64.b64decode(data_dict["data"])
                return np.frombuffer(data_bytes, dtype=np.dtype(data_dict["dtype"])).reshape(data_dict["shape"])
            else:
                # 바이트 데이터로 복원
                return base64.b64decode(data_dict["data"])
                
        except Exception as e:
            logger.error(f"모션 데이터 로드 실패: {str(e)}")
            raise MotionGenerationError(
                message="모션 데이터 로드 중 오류 발생",
                error_code="LOAD_ERROR",
                details={"error": str(e)}
            )

async def generate_animation(prompt: str) -> Dict[str, Any]:
    """
    MDM 모델을 사용하여 애니메이션을 생성합니다.
    
    Args:
        prompt (str): 정제된 프롬프트
        
    Returns:
        Dict[str, Any]: {
            'status': 'success' | 'error',
            'motion_data': Dict,  # 성공 시 모션 데이터
            'metadata': Dict,  # 메타데이터
            'error': str  # 에러 발생 시 에러 메시지
        }
    """
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            # MDM 서버에 요청
            payload = {
                "prompt": prompt,
                "motion_length": 60,  # 기본값
                "num_repetitions": 1,  # 기본값
                "output_format": "json_file"
            }
            
            response = await client.post(
                f"{MDM_SERVER_URL}/predict",
                json=payload
            )
            
            if response.status_code == 200:
                try:
                    # 응답이 JSON 파일이므로 내용을 파싱
                    result = response.json()
                    motion_data = result.get("json_file", {})
                    
                    # 필요한 키가 있는지 확인
                    if not all(key in motion_data for key in ['thetas', 'root_translation', 'joint_map']):
                        raise ValueError("필수 모션 데이터가 누락되었습니다")
                    
                    return {
                        'status': 'success',
                        'motion_data': motion_data,
                        'metadata': {
                            'prompt': prompt,
                            'motion_length': payload['motion_length'],
                            'num_repetitions': payload['num_repetitions']
                        }
                    }
                except json.JSONDecodeError as e:
                    error_msg = f"JSON 파일 파싱 실패: {str(e)}"
                    logger.error(error_msg)
                    return {
                        'status': 'error',
                        'error': error_msg
                    }
                except ValueError as e:
                    error_msg = str(e)
                    logger.error(error_msg)
                    return {
                        'status': 'error',
                        'error': error_msg
                    }
            else:
                error_msg = f"MDM 서버 응답 오류: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return {
                    'status': 'error',
                    'error': error_msg
                }
                
    except httpx.TimeoutException:
        error_msg = "MDM 서버 연결 시간 초과"
        logger.error(error_msg)
        return {
            'status': 'error',
            'error': error_msg
        }
    except Exception as e:
        error_msg = f"MDM 서버 연결 실패: {str(e)}"
        logger.error(error_msg)
        return {
            'status': 'error',
            'error': error_msg
        } 