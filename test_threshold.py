"""
Threshold 기반 필터링 테스트 스크립트

이 스크립트는 유사도 검색 및 threshold 기반 필터링을 테스트합니다.
"""

from agent import search_similar_departments, get_message_content


def main():
    """Threshold 필터링 테스트"""
    print("=" * 60)
    print("Threshold 기반 필터링 테스트")
    print("=" * 60)
    
    # 테스트할 메시지 ID
    msg_id = "8"
    
    # DB에서 메시지 내용 가져오기
    test_content = get_message_content(msg_id)
    
    if not test_content:
        print(f"메시지 ID {msg_id}를 찾을 수 없습니다.")
        return
    
    print(test_content)
   
     
    # Threshold 설정
    threshold = 0
    top_k = 30
    
    print(f"\n메시지 ID: {msg_id}")
    print(f"문의 내용: {test_content}")
    print(f"Threshold: {threshold}")
    print(f"Top K: {top_k}")
    print("-" * 60)
    
    # 유사 부서 검색 (threshold 기반 필터링 포함)
    similar_departments = search_similar_departments(
        content=test_content,
        threshold=threshold,
        top_k=top_k
    )
    
    print(f"\n검색 결과: {len(similar_departments)}개 부서가 threshold({threshold})를 넘었습니다.\n")
    
    if similar_departments:
        print("유사 부서 목록:")
        for i, dept in enumerate(similar_departments, 1):
            print(f"{i}. {dept['dept_name']}")
            print(f"   ID: {dept['dept_id']}")
            print(f"   유사도: {dept['similarity']:.4f}")
            print(f"   설명: {dept.get('dept_desc', 'N/A')}")
            print()
    else:
        print("threshold를 넘는 부서가 없습니다.")
    
    print("=" * 60)
    print("테스트 완료")
    print("=" * 60)


if __name__ == "__main__":
    main()

