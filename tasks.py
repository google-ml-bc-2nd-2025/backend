from celery import shared_task
from celery_app import app  

from agent_manager import generate_with_gemma3
from mdm import generate_animation

@shared_task(bind=True)  # <-- 여기 bind=True를 넣으면 나중에 retry 같은 기능 쓸 수 있어요 (선택사항)
def generate_text_async(self, prompt, model=None, stream=False, service="google"):
    """
    비동기적으로 텍스트를 생성하는 Celery 작업
    """
    try:
        # 텍스트 생성
        text_result = generate_with_gemma3(
            prompt=prompt,
            model=model,
            stream=stream,
            service=service
        )
        
        # MDM 모델을 통한 애니메이션 생성
        try:
            animation_result = generate_animation(text_result['response'])
            return {
                "text_result": text_result,
                "animation_result": animation_result,
                "status": "completed"
            }
        except Exception as animation_error:
            return {
                "text_result": text_result,
                "animation_error": str(animation_error),
                "status": "text_only"
            }
            
    except Exception as e:
        return {"error": str(e), "status": "failed"}

@shared_task
def process_batch_prompts(prompts, model=None, service="google"):
    """
    여러 프롬프트를 배치로 처리하는 Celery 작업
    """
    results = []
    for prompt in prompts:
        try:
            result = generate_text_async.delay(
                prompt=prompt,
                model=model,
                service=service
            )
            results.append({"task_id": result.id})
        except Exception as e:
            results.append({"error": str(e)})
    return results
