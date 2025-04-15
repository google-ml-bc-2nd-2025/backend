"""
에이전트 기본 클래스
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio
import json
from redis.asyncio import Redis
import logging
from enum import Enum

logger = logging.getLogger(__name__)

class EnumEncoder(json.JSONEncoder):
    """Enum 타입을 JSON으로 변환하기 위한 인코더"""
    def default(self, obj):
        if isinstance(obj, Enum):
            return obj.value
        return super().default(obj)

class Message:
    """에이전트 간 통신을 위한 메시지 클래스"""
    def __init__(self, sender: str, intent: str, content: Dict[str, Any]):
        self.sender = sender
        self.intent = intent
        self.content = content
        
    def to_dict(self) -> Dict[str, Any]:
        """메시지를 딕셔너리로 변환"""
        return {
            "sender": self.sender,
            "intent": self.intent,
            "content": self.content
        }
        
    def to_json(self) -> str:
        """메시지를 JSON 문자열로 변환"""
        return json.dumps(self.to_dict(), cls=EnumEncoder)
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """딕셔너리에서 메시지 객체 생성"""
        return cls(
            sender=data["sender"],
            intent=data["intent"],
            content=data["content"]
        )
        
    @classmethod
    def from_json(cls, json_str: str) -> 'Message':
        """JSON 문자열에서 메시지 객체 생성"""
        data = json.loads(json_str)
        return cls.from_dict(data)

class BaseAgent:
    """에이전트 기본 클래스"""
    def __init__(self, agent_id: str, redis_client: Redis):
        self.agent_id = agent_id
        self.redis_client = redis_client
        self.channel = f"agent:{agent_id}"
        self.running = False
        
    async def send_message(self, receiver: str, intent: str, content: Dict[str, Any]):
        """메시지 전송"""
        message = Message(
            sender=self.agent_id,
            intent=intent,
            content=content
        )
        
        # Redis 채널에 메시지 발행
        channel = f"agent:{receiver}"
        await self.redis_client.publish(
            channel,
            message.to_json()
        )
        
        logger.debug(f"메시지 전송: {self.agent_id} -> {receiver}, intent={intent}")
        
    async def process_message(self, message: Message):
        """메시지 처리 (하위 클래스에서 구현)"""
        raise NotImplementedError("하위 클래스에서 구현해야 합니다.")
        
    async def start(self):
        """에이전트 시작"""
        self.running = True
        logger.info(f"에이전트 시작: {self.agent_id}")
        
        while self.running:
            try:
                # 메시지 수신 대기
                message = await self.receive_message()
                if message:
                    await self.process_message(message)
                    
            except Exception as e:
                logger.error(f"메시지 처리 중 오류 발생: {e}", exc_info=True)
                
            await asyncio.sleep(0.1)  # CPU 부하 방지
            
    async def stop(self):
        """에이전트 중지"""
        self.running = False
        logger.info(f"에이전트 중지: {self.agent_id}")
        # Redis 구독 해제
        await self.redis_client.pubsub().unsubscribe(self.channel)

    async def save_state(self):
        """현재 상태 저장"""
        state = self.get_current_state()
        await self.redis_client.set(f"agent:{self.agent_id}:state", json.dumps(state))
    
    async def load_state(self):
        """저장된 상태 로드"""
        state_data = await self.redis_client.get(f"agent:{self.agent_id}:state")
        if state_data:
            self.restore_state(json.loads(state_data))
    
    def get_current_state(self) -> Dict[str, Any]:
        """현재 상태 반환 (하위 클래스에서 구현)"""
        raise NotImplementedError("하위 클래스에서 구현해야 합니다.")
    
    def restore_state(self, state: Dict[str, Any]):
        """상태 복원 (하위 클래스에서 구현)"""
        raise NotImplementedError("하위 클래스에서 구현해야 합니다.")

    async def receive_message(self) -> Optional[Message]:
        """메시지 수신"""
        channel = f"agent:{self.agent_id}"
        
        try:
            pubsub = self.redis_client.pubsub()
            await pubsub.subscribe(channel)
            
            message = await pubsub.get_message(timeout=1.0)
            if message and message["type"] == "message":
                return Message.from_json(message["data"])
                
        except Exception as e:
            logger.error(f"메시지 수신 실패: {e}", exc_info=True)
            
        return None 