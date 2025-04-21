from typing import Optional
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

def refine_prompt(prompt: str) -> str:
    """
    프롬프트를 개선하는 함수입니다.
    
    Args:
        prompt (str): 원본 프롬프트
        
    Returns:
        str: 개선된 프롬프트
    """
    # Google Gemini API를 사용하여 프롬프트 개선
    llm = ChatGoogleGenerativeAI(
        model="gemini-pro",
        temperature=0.7,
        convert_system_message_to_human=True
    )
    
    template = """
    다음 프롬프트를 더 자세하고 명확하게 개선해주세요:
    {prompt}
    
    개선된 프롬프트:
    """
    
    prompt_template = PromptTemplate.from_template(template)
    response = llm.invoke(prompt_template.format(prompt=prompt))
    
    return response.content 