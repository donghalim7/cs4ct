"""
LangGraph 기반 Department Assignment Agent 사용 예제

이 스크립트는 LangGraph를 활용하여 일반 채팅과 부서 배정을 
동적으로 선택하는 예제입니다.
"""

from agent_langgraph import assign_department


def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("LangGraph Department Assignment Agent - 사용 예제")
    print("=" * 60)
    
    # 테스트할 메시지 ID (실제 사용 시 변경 필요)
    test_msg_id = "25908120953"
    
    print(f"\n메시지 ID: {test_msg_id}")
    print("부서 배정 에이전트를 시작합니다...\n")
    print("=" * 60)
    
    # 부서 배정 에이전트 실행
    # LangGraph가 자동으로 의도를 분류하고 적절한 액션 수행
    status = assign_department(
        msg_id=test_msg_id,
        top_k=5  # 검색할 최대 부서 수
    )
    
    print("\n" + "=" * 60)
    print("최종 결과")
    print("=" * 60)
    
    if status == 1:
        print(f"✓ 부서 배정 완료!")
        print("배정된 부서 정보는 assigned_message 테이블을 확인하세요.")
    else:
        print(f"✗ 일반 채팅으로 처리되었습니다.")
        print("   - 부서 배정이 필요하지 않은 문의입니다.")
    
    print("=" * 60)


if __name__ == "__main__":
    main()

