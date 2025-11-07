from supabase_config import get_supabase_client

try:
    supabase = get_supabase_client()
    print("[OK] Supabase 클라이언트 초기화 성공!")
    
    # dept_name 컬럼만 조회
    print("\n부서명(dept_name) 조회 중...")
    try:
        response = supabase.table("department").select("dept_name").execute()
        
        # 응답 상세 정보 출력
        print(f"응답 타입: {type(response)}")
        print(f"응답 데이터 타입: {type(response.data)}")
        print(f"응답 데이터: {response.data}")
        
        if response.data:
            print(f"\n[OK] 총 {len(response.data)}개의 부서명이 조회되었습니다.\n")
            print("=" * 60)
            print("부서명 목록:")
            print("=" * 60)
            
            for i, dept in enumerate(response.data, 1):
                dept_name = dept.get("dept_name", "N/A")
                print(f"{i:2d}. {dept_name}")
            
            print("=" * 60)
        else:
            print("\n[WARNING] response.data가 비어있습니다.")
            print("가능한 원인:")
            print("1. RLS 정책이 활성화되어 있어서 anon key로는 데이터를 읽을 수 없음")
            print("2. 테이블에 실제로 데이터가 없음")
            print("\n해결 방법:")
            print("- Supabase 대시보드 > Authentication > Policies에서")
            print("  department 테이블의 SELECT 정책을 확인/추가하세요")
            print("- 또는 Table Editor에서 RLS를 비활성화하세요 (개발 환경만)")
            
    except Exception as query_error:
        print(f"\n[ERROR] 쿼리 실행 오류:")
        print(f"오류 타입: {type(query_error).__name__}")
        print(f"오류 메시지: {query_error}")
        import traceback
        traceback.print_exc()
        
except Exception as e:
    print(f"\n[ERROR] 전체 오류 발생: {e}")
    import traceback
    traceback.print_exc()
