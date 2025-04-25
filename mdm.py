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

# Redis 연결
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "redis"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    db=int(os.getenv("REDIS_DB", 0)),
    decode_responses=False
)

# MDM 서버 설정
MDM_SERVER_URL = os.getenv("MDM_SERVER_URL", "http://82.141.118.2:2249")  # 마지막 슬래시 제거
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
    generation_time: float
    frame_count: int

    def to_dict(self) -> Dict[str, Any]:
        """메타데이터를 딕셔너리로 변환"""
        return {
            "prompt": self.prompt,
            "generation_time": self.generation_time,
            "frame_count": self.frame_count,
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
    """모션 데이터 생성 및 관리&데이터 저장 및 검색"""
    def __init__(self, model_version: str = "test-v1"):
        pass
    
    def save_motion_data(self, motion_data: Union[np.ndarray, bytes], task_id: str) -> str:
        """모션 데이터를 Redis에 저장하고 키를 반환"""
        try:
            logger.info(f"[SAVE] 모션 데이터 저장 시작 (task_id: {task_id})")
            
            # 고유 키 생성
            data_key = f"motion:{task_id}"
            logger.info(f"[SAVE] Redis 키: {data_key}")
            
            if isinstance(motion_data, np.ndarray):
                data_dict = {
                    "type": "numpy",
                    "shape": motion_data.shape,
                    "dtype": str(motion_data.dtype),
                    "data": base64.b64encode(motion_data.tobytes()).decode('utf-8')
                }
            else:  # bytes 타입인 경우
                data_dict = {
                    "type": "bytes",
                    "length": len(motion_data),
                    "data": base64.b64encode(motion_data).decode('utf-8')
                }
            
            # Redis에 저장 (1시간 유효)
            logger.info(f"[SAVE] Redis 저장 시작")
            redis_client.setex(
                data_key,
                3600,  # 1시간 TTL
                json.dumps(data_dict)
            )
            return data_key
            
        except Exception as e:
            logger.error(f"[SAVE] 모션 데이터 Redis 저장 실패: {str(e)}", exc_info=True)
            raise MotionGenerationError(
                message="모션 데이터 저장 중 오류 발생",
                error_code="SAVE_ERROR",
                details={"error": str(e)}
            )
    
    def load_motion_data(self, data_key: str) -> np.ndarray:
        """Redis에서 모션 데이터를 로드"""
        try:
            data_json = redis_client.get(data_key)
            data_dict = json.loads(data_json)
            data_bytes = base64.b64decode(data_dict["data"])
            return np.frombuffer(data_bytes, dtype=data_dict["dtype"])
        except Exception as e:  
            logger.error(f"모션 데이터 로드 실패: {str(e)}")
            raise MotionGenerationError(
                message="모션 데이터 로드 중 오류 발생",
                error_code="LOAD_ERROR",
                details={"error": str(e)}
            )

async def generate_animation(prompt: str) -> dict:
    """
    프롬프트를 기반으로 모션을 생성합니다.
    
    Args:
        prompt: 사용자 입력 프롬프트
        
    Returns:
        모션 생성 결과
    """
    try:
        # 모션 생성 요청
        print(f"[DEBUG] 모션 생성 요청: prompt={prompt}")
        response = requests.post(
            'http://82.141.118.2:2249/predict',
            json={
                'prompt': prompt,
                'num_repetitions': 1,
                'output_format': 'json_file'
            }
        )
        print(f"[DEBUG] 모션 생성 응답: status_code={response.status_code}")
        print(f"[DEBUG] 모션 생성 응답: content={response.content}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"[DEBUG] 모션 생성 결과: {result}")
            
            # 모션 데이터 변환
            json_file = result.get('json_file', {})
            
            # thetas를 numpy 배열로 변환
            thetas = json_file.get('thetas', [])
            pose_array = np.array(thetas, dtype=np.float32)
            
            # root_translation을 numpy 배열로 변환
            root_translation = json_file.get('root_translation', [])
            trans_array = np.array(root_translation, dtype=np.float32)
            
            # betas는 빈 배열로 설정
            betas_array = np.array([], dtype=np.float32)
            
            # 전체 모션 데이터를 하나의 numpy 배열로 결합
            motion_array = np.concatenate([
                pose_array.reshape(-1),
                betas_array,
                trans_array.reshape(-1)
            ])
            
            return {
                'status': 'success',
                'motion_data': motion_array,
                'metadata': {
                    'pose_shape': pose_array.shape,
                    'trans_shape': trans_array.shape
                }
            }
        else:
            return {
                'status': 'failed',
                'error': f'모션 생성 실패: {response.status_code}'
            }
            
    except Exception as e:
        print(f"[DEBUG] 모션 생성 오류: {str(e)}")
        return {
            'status': 'failed',
            'error': str(e)
        }