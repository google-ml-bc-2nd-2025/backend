"""
Motion Diffusion Model 인터페이스 테스트
"""

import unittest
import numpy as np
from mdm import (
    MotionGenerator,
    MotionData,
    MotionMetadata,
    MotionGenerationError,
    MotionStatus
)

class TestMotionGeneration(unittest.TestCase):
    def setUp(self):
        """각 테스트 전에 실행"""
        self.generator = MotionGenerator(model_version="test-v1")
    
    def test_basic_generation(self):
        """기본적인 모션 생성 테스트"""
        result = self.generator.generate("walk forward")
        
        # 성공 상태 확인
        self.assertEqual(result['status'], 'success')
        
        # 메타데이터 확인
        self.assertIn('metadata', result)
        metadata = result['metadata']
        self.assertEqual(metadata['prompt'], "walk forward")
        self.assertEqual(metadata['model_version'], "test-v1")
        self.assertGreater(metadata['generation_time'], 0)
        
        # 모션 데이터 확인
        self.assertIn('motion_data', result)
        self.assertIsInstance(result['motion_data'], bytes)
    
    def test_empty_prompt(self):
        """빈 프롬프트 처리 테스트"""
        with self.assertRaises(MotionGenerationError) as context:
            self.generator.generate("")
        
        self.assertEqual(context.exception.error_code, "EMPTY_PROMPT")
        self.assertEqual(str(context.exception), "프롬프트가 비어있습니다")
    
    def test_motion_data_validation(self):
        """모션 데이터 유효성 검사 테스트"""
        # 잘못된 형태의 관절 데이터
        invalid_joints = np.random.rand(60, 24)  # 3차원이 아님
        
        with self.assertRaises(ValueError):
            metadata = MotionMetadata(
                prompt="test",
                model_version="test-v1",
                generation_time=1.0,
                frame_count=60
            )
            MotionData(invalid_joints, metadata)
    
    def test_metadata_conversion(self):
        """메타데이터 변환 테스트"""
        metadata = MotionMetadata(
            prompt="test prompt",
            model_version="test-v1",
            generation_time=1.5,
            frame_count=60,
            fps=30.0,
            additional_info={"test_key": "test_value"}
        )
        
        metadata_dict = metadata.to_dict()
        self.assertEqual(metadata_dict['prompt'], "test prompt")
        self.assertEqual(metadata_dict['fps'], 30.0)
        self.assertEqual(metadata_dict['test_key'], "test_value")
    
    def test_motion_data_to_smpl(self):
        """SMPL 형식 변환 테스트"""
        # 테스트용 모션 데이터 생성
        joints = np.random.rand(60, 24, 3)
        metadata = MotionMetadata(
            prompt="test",
            model_version="test-v1",
            generation_time=1.0,
            frame_count=60
        )
        
        motion_data = MotionData(joints, metadata)
        smpl_data = motion_data.to_smpl()
        
        # SMPL 데이터가 올바른 형식인지 확인
        self.assertIsInstance(smpl_data, bytes)
        
        # JSON으로 파싱 가능한지 확인
        import json
        parsed_data = json.loads(smpl_data.decode())
        self.assertIn('joints', parsed_data)
        self.assertIn('metadata', parsed_data)

if __name__ == '__main__':
    unittest.main() 