"""
Department Assignment Agent 사용 예제

이 스크립트는 고객 문의를 부서에 자동으로 배정하는 예제입니다.
"""

from agent import assign_department


def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("Department Assignment Agent - 사용 예제")
    print("=" * 60)
    
    # 테스트할 메시지 ID (실제 사용 시 변경 필요)
    test_msg_id = "test_message_001"
    
    print(f"\n메시지 ID: {test_msg_id}")
    print("부서 배정을 시작합니다...\n")
    
    # 부서 배정 실행
    status = assign_department(
        msg_id=test_msg_id,
        threshold=0.7,  # 유사도 임계값
        top_k=5         # 검색할 최대 부서 수
    )
    
    print("\n" + "=" * 60)
    print("배정 결과")
    print("=" * 60)
    
    if status == 1:
        print(f"✓ 상태: 정상 처리 완료")
        print("\n배정이 성공적으로 완료되었습니다!")
        print("배정된 부서 정보는 assigned_message 테이블을 확인하세요.")
    else:
        print(f"✗ 상태: 비정상 문의")
        print(f"✗ 사유: threshold({0.7})를 넘는 유사 부서가 없습니다.")
        print("\n문의 내용을 검토해주세요.")
    
    print("=" * 60)


if __name__ == "__main__":
    main()
