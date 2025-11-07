# CS4CT - Department Assignment Agent

KURE 임베딩 모델과 GPT-4 mini를 활용한 고객 문의 부서 자동 배정 시스템

## 개요

이 시스템은 고객 문의 내용을 분석하여 적절한 부서에 자동으로 배정합니다.
- **임베딩 모델**: KURE-v1 (한국어 특화 임베딩)
- **LLM**: GPT-4 mini
- **데이터베이스**: Supabase

## 설치

1. 의존성 설치:
```bash
pip install -e .
```

2. 환경변수 설정:

`env.template` 파일을 참고하여 `.env` 파일을 생성하세요:

```bash
cp env.template .env
```

`.env` 파일에 다음 정보를 입력하세요:
```
SUPABASE_URL=your_supabase_url_here
SUPABASE_KEY=your_supabase_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

## 데이터베이스 구조

### 필요한 테이블

1. **message 테이블**
   - `msg_id` (TEXT, PRIMARY KEY)
   - `content` (TEXT)

2. **department 테이블**
   - `dept_id` (TEXT, PRIMARY KEY)
   - `dept_name` (TEXT)
   - `dept_desc` (TEXT)

3. **assigned_message 테이블**
   - `msg_id` (TEXT, FOREIGN KEY)
   - `dept_id` (TEXT, FOREIGN KEY)

### 검색 방식

현재 시스템은 다음과 같이 작동합니다:
1. Supabase에서 모든 부서의 `dept_name`과 `dept_desc`를 조회
2. 각 부서의 텍스트를 KURE 모델로 임베딩 생성
3. 사용자 문의와 코사인 유사도 계산
4. threshold를 넘는 부서만 필터링하여 반환

**참고**: 부서가 많은 경우 성능 최적화를 위해 department 테이블에 미리 생성된 임베딩 벡터를 저장하고 pgvector를 활용하는 것을 권장합니다.

## 사용 방법

### 기본 사용

```python
from agent import assign_department

# 메시지 ID로 부서 배정
status = assign_department(
    msg_id="message_123",
    threshold=0.7,  # 유사도 임계값 (기본값: 0.7)
    top_k=5         # 검색할 최대 부서 수 (기본값: 5)
)

if status == 1:
    print("배정 완료! assigned_message 테이블을 확인하세요.")
else:
    print("비정상 문의입니다. (threshold를 넘는 유사 부서 없음)")
```

### 반환 값

- `status == 0`: 비정상 문의 (threshold를 넘는 유사 부서가 없음)
- `status == 1`: 정상 처리 완료 (배정된 부서는 assigned_message 테이블에 저장됨)

### 개별 함수 사용

```python
from agent import (
    get_message_content,
    search_similar_departments,
    select_departments_with_llm,
    save_assignment
)

# 1. 메시지 조회
content = get_message_content("msg_123")

# 2. 유사 부서 검색
candidates = search_similar_departments(content, threshold=0.7, top_k=5)

# 3. LLM으로 부서 선택
selected_ids = select_departments_with_llm(content, candidates)

# 4. 결과 저장
save_assignment("msg_123", selected_ids)
```

## 특징

1. **한국어 특화**: KURE-v1 모델 사용으로 한국어 문의 처리에 최적화
2. **Threshold 기반 필터링**: 유사도가 낮은 경우 비정상 문의로 판단
3. **LLM 기반 선택**: GPT-4 mini가 문맥을 이해하고 최적의 부서 선택
4. **다중 부서 배정**: 여러 부서가 관련된 경우 모두 배정 가능
5. **자동 DB 저장**: 배정 결과를 자동으로 Supabase에 저장
6. **Fail-fast 설계**: 의도하지 않은 오류 발생 시 즉시 예외를 발생시켜 디버깅 용이

## 참고 자료

- [KURE 임베딩 모델](https://github.com/nlpai-lab/KURE)
- [OpenAI API](https://platform.openai.com/docs)
- [Supabase 문서](https://supabase.com/docs)