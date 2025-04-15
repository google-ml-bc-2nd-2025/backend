"""
TaskExecutor 통합 테스트 모듈
"""

import pytest
import asyncio
import numpy as np
from pathlib import Path
from src.agents.task_executor import TaskExecutor
from src.agents.base import Message, BaseAgent
import json
import redis
from unittest.mock import AsyncMock, MagicMock, call

class MockController(BaseAgent):
    """컨트롤러 모의 객체"""
    def __init__(self):
        super().__init__("controller", None)
        self.received_messages = []
        
    async def send_message(self, receiver: str, intent: str, content: dict):
        self.received_messages.append({
            "receiver": receiver,
            "intent": intent,
            "content": content
        })

@pytest.fixture
def redis_client():
    """Redis 클라이언트 모의 객체"""
    mock = MagicMock(spec=redis.Redis)
    mock.publish = AsyncMock()
    return mock

@pytest.fixture
def mock_controller():
    """컨트롤러 모의 객체 생성"""
    return MockController()

@pytest.fixture
def task_executor(redis_client, tmp_path):
    """TaskExecutor 인스턴스 생성"""
    executor = TaskExecutor(redis_client, str(tmp_path))
    executor.redis_client = redis_client
    return executor

@pytest.fixture
def sample_workflow():
    """샘플 워크플로우 데이터"""
    # 테스트 데이터 생성
    test_data = {
        "poses": np.random.rand(60, 72),  # 60프레임, 72차원 포즈 데이터
        "fps": 30.71428623734689
    }
    
    # 테스트 데이터 저장
    test_data_path = Path("test_data")
    test_data_path.mkdir(exist_ok=True)
    np.save(test_data_path / "walking_back_smpl.npy", test_data)
    
    return {
        "steps": [
            {
                "step_id": "prepare_motion",
                "action": "prepare_motion_data",
                "params": {
                    "emotion": "neutral",
                    "motion_type": "walking",
                    "input_file": str(test_data_path / "walking_back_smpl.npy")
                }
            },
            {
                "step_id": "create_animation",
                "action": "create_animation",
                "params": {
                    "style": "default"
                }
            },
            {
                "step_id": "post_process",
                "action": "apply_post_processing",
                "params": {
                    "effects": ["smooth"]
                }
            }
        ],
        "resources": {
            "prepare_motion": {"cpu": 0.3, "gpu": 0.2},
            "create_animation": {"cpu": 0.4, "gpu": 0.3},
            "post_process": {"cpu": 0.2, "gpu": 0.1}
        },
        "metadata": {
            "duration": 1.0,
            "fps": 30.71428623734689
        }
    }

@pytest.fixture(autouse=True)
def cleanup_test_data():
    """테스트 데이터 정리"""
    yield
    test_data_path = Path("test_data")
    if test_data_path.exists():
        for file in test_data_path.glob("*.npy"):
            file.unlink()
        test_data_path.rmdir()

@pytest.mark.asyncio
async def test_workflow_execution_flow(task_executor, mock_controller, sample_workflow):
    """워크플로우 실행 흐름 테스트"""
    # 워크플로우 실행 메시지 생성
    message = Message(
        sender="controller",
        intent="execute_workflow",
        content={
            "task_id": "test_task",
            "workflow": sample_workflow,
            "original_prompt": "뒤로 걷는 모션을 만들어주세요"
        }
    )
    
    # 워크플로우 실행
    await task_executor.process_message(message)
    
    # 상태 업데이트 메시지 확인
    publish_calls = task_executor.redis_client.publish.call_args_list
    status_updates = [
        json.loads(call[0][1])
        for call in publish_calls
        if json.loads(call[0][1])["intent"] == "status_update"
    ]
    assert len(status_updates) > 0
    
    # 최종 상태 확인
    final_status = status_updates[-1]["content"]
    assert final_status["status"] == "completed"
    assert final_status["progress"] == 100.0
    
    # 결과 디렉토리 확인
    task_dir = task_executor.output_dir / "test_task"
    assert task_dir.exists()
    
    # 결과 파일 확인
    assert (task_dir / "animation.npy").exists()
    assert (task_dir / "metadata.json").exists()
    
    # 결과 데이터 검증
    result_data = np.load(task_dir / "animation.npy", allow_pickle=True).item()
    assert isinstance(result_data, dict)
    assert "poses" in result_data
    assert "fps" in result_data
    assert result_data["fps"] == sample_workflow["metadata"]["fps"]
    
    # 메타데이터 검증
    with open(task_dir / "metadata.json", "r") as f:
        metadata = json.load(f)
    assert metadata["fps"] == sample_workflow["metadata"]["fps"]
    assert "effects" in metadata

@pytest.mark.asyncio
async def test_error_handling_flow(task_executor, mock_controller):
    """오류 처리 흐름 테스트"""
    # 잘못된 워크플로우로 메시지 생성
    message = Message(
        sender="controller",
        intent="execute_workflow",
        content={
            "task_id": "test_task",
            "workflow": {},  # 잘못된 워크플로우
            "original_prompt": "테스트"
        }
    )
    
    # 워크플로우 실행
    await task_executor.process_message(message)
    
    # 오류 메시지 확인
    publish_calls = task_executor.redis_client.publish.call_args_list
    error_messages = [
        json.loads(call[0][1])
        for call in publish_calls
        if json.loads(call[0][1])["intent"] == "execution_error"
    ]
    assert len(error_messages) == 1
    
    # 오류 내용 확인
    error_content = error_messages[0]["content"]
    assert error_content["task_id"] == "test_task"
    assert "error" in error_content

@pytest.mark.asyncio
async def test_concurrent_workflow_execution(task_executor, sample_workflow):
    """동시 워크플로우 실행 테스트"""
    # 여러 워크플로우 동시 실행
    tasks = []
    for i in range(3):
        message = Message(
            sender="controller",
            intent="execute_workflow",
            content={
                "task_id": f"test_task_{i}",
                "workflow": sample_workflow,
                "original_prompt": f"테스트 {i}"
            }
        )
        tasks.append(task_executor.process_message(message))
    
    # 모든 워크플로우 실행 완료 대기
    await asyncio.gather(*tasks)
    
    # 각 워크플로우 결과 확인
    for i in range(3):
        task_dir = task_executor.output_dir / f"test_task_{i}"
        assert task_dir.exists()
        assert (task_dir / "animation.npy").exists()
        assert (task_dir / "metadata.json").exists()

@pytest.mark.asyncio
async def test_resource_management(task_executor, sample_workflow):
    """리소스 관리 테스트"""
    # 리소스 사용량 초기화
    task_executor.resource_usage = {"cpu": 0.7, "gpu": 0.6}
    
    # 워크플로우 실행 시도
    message = Message(
        sender="controller",
        intent="execute_workflow",
        content={
            "task_id": "test_task",
            "workflow": sample_workflow,
            "original_prompt": "테스트"
        }
    )
    
    # 워크플로우 실행
    await task_executor.process_message(message)
    
    # 오류 메시지 확인
    publish_calls = task_executor.redis_client.publish.call_args_list
    error_messages = [
        json.loads(call[0][1])
        for call in publish_calls
        if json.loads(call[0][1])["intent"] == "execution_error"
    ]
    assert len(error_messages) == 1
    
    # 오류 내용에 리소스 부족 메시지가 포함되어 있는지 확인
    error_content = error_messages[0]["content"]
    assert "리소스 부족" in error_content["error"]

@pytest.mark.asyncio
async def test_workflow_cancellation(task_executor, sample_workflow):
    """워크플로우 취소 테스트"""
    # 워크플로우 실행 시작
    message = Message(
        sender="controller",
        intent="execute_workflow",
        content={
            "task_id": "test_task",
            "workflow": sample_workflow,
            "original_prompt": "테스트"
        }
    )

    # 워크플로우 실행 시작
    task = asyncio.create_task(task_executor.process_message(message))

    # 잠시 대기 후 취소
    await asyncio.sleep(0.1)
    
    # 취소 메시지 전송
    cancel_message = Message(
        sender="controller",
        intent="cancel_workflow",
        content={
            "task_id": "test_task"
        }
    )
    await task_executor.process_message(cancel_message)
    
    # 작업 완료 대기
    try:
        await task
    except asyncio.CancelledError:
        pass

    # 상태 업데이트 메시지 확인
    publish_calls = task_executor.redis_client.publish.call_args_list
    status_updates = [
        json.loads(call[0][1])
        for call in publish_calls
        if json.loads(call[0][1])["intent"] == "status_update"
    ]

    # 디버깅을 위한 상태 업데이트 로그 출력
    print("\n상태 업데이트 메시지:")
    for update in status_updates:
        print(f"Status: {update['content']['status']}, Progress: {update['content']['progress']}")

    # 마지막 상태가 cancelled인지 확인
    assert len(status_updates) > 0, "상태 업데이트가 없습니다"
    assert any(
        update["content"]["status"] == "cancelled"
        for update in status_updates
    ), "취소 상태가 없습니다" 