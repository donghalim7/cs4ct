# cs4ct

CS 관리 시스템 - Streamlit 기반 대시보드

## 설치 방법

1. 의존성 설치
```bash
# Windows의 경우
py -m pip install -r requirements.txt

# Linux/Mac의 경우
pip install -r requirements.txt
```

2. 환경 변수 설정
`.env` 파일을 생성하고 Supabase anon key를 설정하세요:
```
SUPABASE_KEY=your_supabase_anon_key_here
```

3. 앱 실행
```bash
# Windows의 경우
py -m streamlit run app.py

# Linux/Mac의 경우
streamlit run app.py
```

## 사용 방법

1. **페이지 1: 회사 선택**
   - A사, B사, C사 중 하나를 선택하여 해당 회사의 현황 버튼 클릭

2. **페이지 2: 회사 대시보드**
   - 왼쪽: 부서 목록 (마케팅팀, 영업팀, 개발팀 등)
   - 오른쪽: 최근 들어온 CS 리스트, CS가 가장 많이 배정된 부서 통계
   - 부서 대시보드 버튼 클릭하여 상세 페이지로 이동

3. **페이지 3: 부서 상세 대시보드**
   - 최상단: 최근 배정된 CS 큐 테이블
   - 통계 카드: 총 배정된 CS, 완료된 CS, 완료율
   - 그래프: CS 완료율 추이, 팀원별 배정 현황, 카테고리별 통계 등

## Supabase 데이터베이스 구조

- **assigned_message**: CS 배정 정보 (dept_id, msg_id)
- **department**: 부서 정보 (dept_id, dept_name, dept_desc)
- **message**: CS 메시지 내용 (msg_id, content)

## Project ID
ewftdvslhefeipjpkvnf