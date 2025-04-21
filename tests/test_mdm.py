import pytest
from mdm import generate_animation
import asyncio

async def test_generate_animation():
    """MDM 모델 애니메이션 생성 테스트"""
    # 테스트용 프롬프트
    prompt = "A person walks forward slowly with a relaxed posture"
    
    # 애니메이션 생성 테스트
    result = await generate_animation(prompt)
    
    # 응답 검증
    assert isinstance(result, dict)
    assert 'status' in result
    
    if result['status'] == 'success':
        assert 'motion_data' in result
        assert 'metadata' in result
        assert result['metadata']['prompt'] == prompt
    else:
        assert 'error' in result

def test_generate_animation_sync():
    """동기 방식으로 테스트 실행을 위한 래퍼"""
    asyncio.run(test_generate_animation()) 