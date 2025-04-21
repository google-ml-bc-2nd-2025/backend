import pytest
from agent.think import check_prompt
from agent.state import PromptState

def test_check_prompt_valid():
    """유효한 프롬프트 테스트"""
    prompt = "고양이가 공원에서 놀고 있는 모습을 만들어주세요"
    result = check_prompt(prompt)
    
    assert isinstance(result, PromptState)
    assert result.is_valid is True
    assert result.error_message is None

def test_check_prompt_too_short():
    """너무 짧은 프롬프트 테스트"""
    prompt = "고양이"
    result = check_prompt(prompt)
    
    assert result.is_valid is False
    assert "너무 짧습니다" in result.error_message

def test_check_prompt_special_chars():
    """특수문자가 포함된 프롬프트 테스트"""
    prompt = "고양이@공원"
    result = check_prompt(prompt)
    
    assert result.is_valid is False
    assert "특수문자" in result.error_message

def test_check_prompt_inappropriate():
    """부적절한 내용이 포함된 프롬프트 테스트"""
    prompt = "해킹하는 고양이"
    result = check_prompt(prompt)
    
    assert result.is_valid is False
    assert "부적절한 내용" in result.error_message 