from agent.state import AgentState

def work_step(state: AgentState) -> AgentState:
    """작업 단계: 실제 게임 리소스 생성 작업 수행"""
    resource_type = state.get("resource_type", "other")
    
    if resource_type == "3d_model":
        work_results = """
        [3D 모델 생성 결과]
        - 파일 형식: FBX, OBJ, GLTF
        - 폴리곤 수: 15,420
        - 텍스처 맵: Diffuse, Normal, Roughness, Metallic
        - 리깅: 완료
        - 미리보기 URL: https://example.com/preview/model123.jpg
        - 다운로드 URL: https://example.com/download/model123.zip
        
        모델이 성공적으로 생성되었습니다. 위 URL에서 확인하고 다운로드할 수 있습니다.
        """
    elif resource_type == "animation":
        work_results = """
        [애니메이션 생성 결과]
        - 파일 형식: FBX, BVH
        - 프레임 수: 120
        - 애니메이션 길이: 4초
        - 애니메이션 유형: 걷기/달리기 사이클
        - 미리보기 URL: https://example.com/preview/anim123.gif
        - 다운로드 URL: https://example.com/download/anim123.zip
        
        애니메이션이 성공적으로 생성되었습니다. 위 URL에서 확인하고 다운로드할 수 있습니다.
        """
    else:
        work_results = "지원되지 않는 리소스 유형입니다."
    
    return {
        **state,
        "work_results": work_results,
        "next": "answer_step"
    }