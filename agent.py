import os
import json
from typing import List, Optional
from dotenv import load_dotenv
from supabase import create_client, Client
from sentence_transformers import SentenceTransformer
from openai import OpenAI
import numpy as np


# 환경변수 로드
load_dotenv()

# 전역 변수
_embedding_model = None
_supabase_client = None
_openai_client = None


def get_supabase_client() -> Client:
    """Supabase 클라이언트 초기화 및 반환"""
    global _supabase_client
    if _supabase_client is None:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        if not url or not key:
            raise ValueError("SUPABASE_URL 및 SUPABASE_KEY 환경변수가 필요합니다.")
        _supabase_client = create_client(url, key)
    return _supabase_client


def get_openai_client() -> OpenAI:
    """OpenAI 클라이언트 초기화 및 반환"""
    global _openai_client
    if _openai_client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY 환경변수가 필요합니다.")
        _openai_client = OpenAI(api_key=api_key)
    return _openai_client


def load_embedding_model() -> SentenceTransformer:
    """KURE-v1 임베딩 모델 로드"""
    global _embedding_model
    if _embedding_model is None:
        print("KURE-v1 임베딩 모델을 로딩 중입니다...")
        _embedding_model = SentenceTransformer("nlpai-lab/KURE-v1")
        print("모델 로딩 완료!")
    return _embedding_model


def get_message_content(msg_id: str) -> Optional[str]:
    """
    Supabase msg 테이블에서 msg_id로 content 조회
    
    Args:
        msg_id: 메시지 ID
        
    Returns:
        메시지 내용 (content) 또는 None (메시지가 존재하지 않을 때)
    """
    supabase = get_supabase_client()
    response = supabase.table("message").select("content").eq("msg_id", msg_id).execute()
    
    if response.data and len(response.data) > 0:
        return response.data[0]["content"]
    return None


def search_similar_departments(
    content: str, 
    threshold: float, 
    top_k: int
) -> List[dict]:
    """
    KURE 임베딩을 사용하여 유사한 부서 검색
    
    Args:
        content: 검색할 메시지 내용
        threshold: 유사도 임계값 (0-1)
        top_k: 반환할 최대 결과 수
        
    Returns:
        유사 부서 리스트 [{"dept_id": ..., "dept_name": ..., "dept_desc": ..., "similarity": ...}]
        threshold를 넘는 부서가 없으면 빈 리스트 반환
    """
    # 임베딩 모델 로드
    model = load_embedding_model()
    
    # content를 임베딩으로 변환
    query_embedding = model.encode(content)
    
    supabase = get_supabase_client()
    
    # TODO: department 테이블로 변경
    # 부서 정보 조회
    all_departments = supabase.table("department_imsi").select(
        "dept_id, dept_name, dept_desc"
    ).execute()
    
    assert all_departments.data, "부서 정보가 없습니다."
    
    # 각 부서의 이름과 설명을 조합하여 임베딩 생성
    dept_texts = [
        f"{dept['dept_name']} {dept['dept_desc']}"
        for dept in all_departments.data
    ]
    
    # 모든 부서 텍스트를 KURE 모델로 임베딩
    dept_embeddings = model.encode(dept_texts)
    
    # Cosine similarity 계산 (벡터화)
    similarities = np.dot(dept_embeddings, query_embedding) / (
        np.linalg.norm(dept_embeddings, axis=1) * np.linalg.norm(query_embedding)
    )
    
    # threshold를 넘는 결과만 필터링
    results = []
    for i, dept in enumerate(all_departments.data):
        similarity = float(similarities[i])
        if similarity >= threshold:
            results.append({
                "dept_id": dept["dept_id"],
                "dept_name": dept["dept_name"],
                "dept_desc": dept["dept_desc"],
                "similarity": similarity
            })
    
    # 유사도 순으로 정렬하고 top_k개만 반환
    results.sort(key=lambda x: x["similarity"], reverse=True)
    return results[:top_k]


def select_departments_with_llm(
    content: str, 
    candidates: List[dict]
) -> List[str]:
    """
    GPT-4 mini를 사용하여 최적의 부서 선택
    
    Args:
        content: 사용자 문의 내용
        candidates: 후보 부서 리스트
        
    Returns:
        선택된 부서 ID 리스트
    """
    client = get_openai_client()
    
    # 후보 부서 정보를 프롬프트에 포함
    candidates_text = "\n".join([
        f"- ID: {dept['dept_id']}, 이름: {dept['dept_name']}, 설명: {dept['dept_desc']}"
        for dept in candidates
    ])
    
    prompt = f"""당신은 고객 문의를 적절한 부서에 배정하는 AI 어시스턴트입니다.

고객 문의 내용:
{content}

후보 부서 목록:
{candidates_text}

위 고객 문의를 처리하기에 가장 적합한 부서를 1개 이상 선택해주세요.
여러 부서가 관련되어 있다면 모두 선택할 수 있습니다.

응답은 반드시 다음 JSON 형식으로만 작성해주세요:
{{"dept_ids": ["선택된_부서_ID1", "선택된_부서_ID2", ...]}}

JSON만 응답하고 다른 설명은 포함하지 마세요."""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "당신은 고객 문의를 적절한 부서에 배정하는 전문가입니다."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        response_format={"type": "json_object"}
    )
    
    result = response.choices[0].message.content
    parsed = json.loads(result)
    
    if "dept_ids" in parsed and parsed["dept_ids"]:
        return parsed["dept_ids"]
    
    raise ValueError(f"LLM이 유효한 부서를 선택하지 못했습니다. 응답: {result}")


def save_assignment(msg_id: str, dept_ids: List[str]) -> None:
    """
    assigned_message 테이블에 배정 결과 저장
    
    Args:
        msg_id: 메시지 ID
        dept_ids: 배정할 부서 ID 리스트
    """
    supabase = get_supabase_client()
    
    # 각 부서에 대해 레코드 삽입
    for dept_id in dept_ids:
        supabase.table("assigned_message").insert({
            "msg_id": msg_id,
            "dept_id": dept_id
        }).execute()


def assign_department(
    msg_id: str, 
    threshold: float = 0.7, 
    top_k: int = 5
) -> int:
    """
    메시지를 분석하여 적절한 부서에 배정
    
    Args:
        msg_id: 메시지 ID
        threshold: 유사도 임계값 (기본값: 0.7)
        top_k: 검색할 최대 부서 수 (기본값: 5)
        
    Returns:
        0: 비정상 문의 (threshold를 넘는 부서가 없음)
        1: 정상 처리 완료 (부서 배정 성공)
    """
    # 1. 메시지 내용 조회
    content = get_message_content(msg_id)
    if not content:
        print(f"메시지 ID {msg_id}를 찾을 수 없습니다.")
        return 0
    
    print(f"문의 내용: {content}")
    
    # 2. 유사 부서 검색
    similar_departments = search_similar_departments(content, threshold, top_k)
    
    # 3. threshold 기반 필터링
    if not similar_departments:
        print("유사도가 threshold를 넘는 부서가 없습니다. (비정상 문의)")
        return 0
    
    print(f"검색된 유사 부서 수: {len(similar_departments)}")
    for dept in similar_departments:
        print(f"  - {dept['dept_name']} (유사도: {dept['similarity']})")
    
    # 4. LLM을 사용하여 최적 부서 선택
    selected_dept_ids = select_departments_with_llm(content, similar_departments)
    print(f"선택된 부서 ID: {selected_dept_ids}")
    
    # 5. 배정 결과 저장
    save_assignment(msg_id, selected_dept_ids)
    
    # 6. 성공적으로 처리
    return 1

