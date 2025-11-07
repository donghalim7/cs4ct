import os
import json
from typing import List, Optional, TypedDict
from dotenv import load_dotenv
from supabase import create_client, Client
from sentence_transformers import SentenceTransformer
from openai import OpenAI
import numpy as np
from langgraph.graph import StateGraph, END
from langchain_core.messages import ToolMessage, SystemMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool


# 환경변수 로드
load_dotenv()

# 전역 변수
_embedding_model = None
_supabase_client = None
_openai_client = None


# ============================================================================
# State 정의
# ============================================================================

class AgentState(TypedDict, total=False):
    """LangGraph Agent 상태"""
    messages: List  # 메시지 리스트
    msg_id: str  # 메시지 ID
    top_k: int  # 검색할 부서 수


# ============================================================================
# Helper 함수들
# ============================================================================

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
    """Supabase message 테이블에서 msg_id로 content 조회"""
    supabase = get_supabase_client()
    response = supabase.table("message").select("content").eq("msg_id", msg_id).execute()
    
    if response.data and len(response.data) > 0:
        return response.data[0]["content"]
    return None


# ============================================================================
# LangChain Tools 정의
# ============================================================================

@tool
def assign_department_tool(query: str, msg_id: str, top_k: int) -> dict:
    """
    고객 문의를 분석하여 적절한 부서에 배정합니다.
    
    Args:
        query: 고객 문의 내용
        msg_id: 메시지 ID
        top_k: 검색할 최대 부서 수
        
    Returns:
        배정 결과 (성공 시 배정된 부서 정보, 실패 시 오류 메시지)
    """
    try:
        print(f"부서 배정 도구 실행: query='{query[:50]}...', top_k={top_k}")
        
        # 임베딩 모델 로드
        model = load_embedding_model()
        
        # content를 임베딩으로 변환
        query_embedding = model.encode(query)
        
        supabase = get_supabase_client()
        
        # 부서 정보 조회
        all_departments = supabase.table("department").select(
            "dept_id, dept_name, dept_desc"
        ).execute()
        
        if not all_departments.data:
            return {"error": "부서 정보가 없습니다."}
        
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
        
        # 모든 부서의 유사도를 계산
        results = []
        for i, dept in enumerate(all_departments.data):
            similarity = float(similarities[i])
            results.append({
                "dept_id": dept["dept_id"],
                "dept_name": dept["dept_name"],
                "dept_desc": dept["dept_desc"],
                "similarity": similarity
            })
        
        # 유사도 순으로 정렬하고 top_k개만 선택
        results.sort(key=lambda x: x["similarity"], reverse=True)
        similar_departments = results[:top_k]
        
        print(f"검색된 유사 부서 수: {len(similar_departments)}")
        for dept in similar_departments:
            print(f"  - {dept['dept_name']} (ID: {dept['dept_id']}, 유사도: {dept['similarity']:.4f})")
        
        # LLM으로 최적 부서 선택
        client = get_openai_client()
        
        candidates_text = "\n".join([
            f"- ID: {dept['dept_id']}, 이름: {dept['dept_name']}, 설명: {dept['dept_desc']}"
            for dept in similar_departments
        ])
        
        prompt = f"""당신은 고객 문의를 적절한 부서에 배정하는 AI 어시스턴트입니다.

고객 문의 내용:
{query}

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
        
        if "dept_ids" not in parsed or not parsed["dept_ids"]:
            return {"error": "LLM이 유효한 부서를 선택하지 못했습니다."}
        
        selected_dept_ids = parsed["dept_ids"]
        print(f"선택된 부서 ID: {selected_dept_ids}")
        
        # DB에 저장 (중복 시 무시)
        for dept_id in selected_dept_ids:
            try:
                supabase.table("assigned_message").insert({
                    "msg_id": msg_id,
                    "dept_id": dept_id
                }).execute()
            except Exception as e:
                # 중복 키 에러는 무시하고 계속 진행
                if "duplicate key" in str(e).lower() or "23505" in str(e):
                    print(f"  ⚠️  부서 {dept_id}는 이미 배정되어 있습니다. (스킵)")
                else:
                    # 다른 에러는 다시 발생
                    raise
        
        # 선택된 부서 정보 반환
        selected_depts = [d for d in similar_departments if d["dept_id"] in selected_dept_ids]
        
        return {
            "success": True,
            "assigned_departments": selected_depts,
            "message": f"{len(selected_dept_ids)}개 부서에 배정되었습니다."
        }
        
    except Exception as e:
        print(f"부서 배정 도구 오류: {e}")
        import traceback
        traceback.print_exc()
        return {"error": f"부서 배정 중 오류 발생: {str(e)}"}


# ============================================================================
# CustomToolNode
# ============================================================================

class CustomToolNode:
    """Custom implementation of ToolNode"""
    
    def __init__(self, tools: list) -> None:
        self.tools = tools
        self.tools_dict = {tool.name: tool for tool in tools}
        
    def __call__(self, state):
        messages = state.get("messages", [])
        msg_id = state.get("msg_id")
        top_k = state.get("top_k", 5)
        
        if not messages:
            return state
            
        # 마지막 메시지에서 tool_calls 추출
        message = messages[-1]
        
        if not hasattr(message, "tool_calls") and not (isinstance(message, dict) and message.get("tool_calls")):
            return state
            
        tool_calls = (message.tool_calls if hasattr(message, "tool_calls") 
                     else message.get("tool_calls", []))
        
        if not tool_calls:
            return state
            
        # Tool 실행
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.get("name") if isinstance(tool_call, dict) else tool_call.name
            tool_args = tool_call.get("args") if isinstance(tool_call, dict) else tool_call.args
            tool_id = tool_call.get("id") if isinstance(tool_call, dict) else tool_call.id
            
            print(f"도구 실행: {tool_name}")
            
            tool = self.tools_dict.get(tool_name)
            
            if not tool:
                print(f"도구를 찾을 수 없음: {tool_name}")
                continue
                
            try:
                final_args = dict(tool_args) if isinstance(tool_args, dict) else {}
                
                # assign_department_tool에 state 정보 주입
                if tool_name == "assign_department_tool":
                    final_args["msg_id"] = msg_id
                    final_args["top_k"] = top_k
                    
                result = tool.invoke(final_args)
                
                results.append(
                    ToolMessage(
                        content=json.dumps(result, ensure_ascii=False),
                        name=tool_name,
                        tool_call_id=tool_id,
                    )
                )
            except Exception as e:
                print(f"도구 실행 오류 {tool_name}: {e}")
                import traceback
                traceback.print_exc()
                
                results.append(
                    ToolMessage(
                        content=f"오류: {str(e)}",
                        name=tool_name,
                        tool_call_id=tool_id,
                    )
                )
        
        return {"messages": results}


# ============================================================================
# 노드 함수들
# ============================================================================

def create_chatbot_node(tools):
    """챗봇 노드 생성"""
    
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.1,
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )
    
    # Tool 설명 생성
    tool_descriptions = []
    for tool in tools:
        tool_descriptions.append(f"- {tool.name}: {tool.description}")
    
    # 시스템 프롬프트
    system_prompt = f"""당신은 친절한 고객 서비스 어시스턴트입니다.

사용 가능한 도구:
{chr(10).join(tool_descriptions)}

**도구 사용 가이드:**

1. **assign_department_tool**: 고객이 구체적인 업무 처리나 문제 해결을 요청할 때 사용
   - 예: "급여 관련 문의입니다", "제품 불량이 발생했습니다", "시스템 오류가 있어요"
   - 회사의 특정 부서에서 처리해야 할 실질적인 업무/문제가 있을 때 사용
   
2. **일반 대화**: 도구를 사용하지 않고 직접 응답
   - 예: "안녕하세요", "감사합니다"
   - 업무 처리가 필요 없는 인사, 감사, 일반 질문

**중요**: 도구가 필요한 경우에만 사용하세요. 간단한 대화는 직접 응답하세요."""

    llm_with_tools = llm.bind_tools(tools)
    
    def chatbot(state: AgentState):
        messages = state["messages"]
        
        # 마지막 사용자 메시지 추출
        last_user_message = None
        for msg in reversed(messages):
            if isinstance(msg, dict) and msg.get("role") == "user":
                last_user_message = msg.get("content", "")
                break
            elif hasattr(msg, "role") and msg.role == "user":
                if hasattr(msg, "content"):
                    last_user_message = msg.content
                    break
        
        print(f"처리 중인 메시지: {last_user_message}")
        
        # 시스템 메시지 추가
        system_msg = SystemMessage(content=system_prompt)
        messages_with_system = [system_msg] + messages
        
        # LLM 호출
        try:
            response = llm_with_tools.invoke(messages_with_system)
            print(f"LLM 응답 타입: {type(response)}")
            print(f"LLM 응답 내용: {response.content if hasattr(response, 'content') else response}")
            if hasattr(response, "tool_calls"):
                print(f"Tool calls: {response.tool_calls}")
        except Exception as e:
            print(f"LLM 호출 오류: {e}")
            response = AIMessage(content="처리 중 오류가 발생했습니다. 다시 시도해 주세요.")
        
        return {"messages": [response]}
    
    return chatbot


def llm_tool_router(state: AgentState):
    """LLM의 응답에 tool_calls가 있는지 확인하여 라우팅"""
    messages = state.get("messages", [])
    
    if not messages:
        return "end"
    
    last_message = messages[-1]
    
    has_tool_calls = False
    if hasattr(last_message, "tool_calls"):
        has_tool_calls = bool(last_message.tool_calls)
    elif isinstance(last_message, dict) and last_message.get("tool_calls"):
        has_tool_calls = bool(last_message.get("tool_calls"))
    
    print(f"Tool calls 존재 여부: {has_tool_calls}")
    
    if has_tool_calls:
        return "tools"
    else:
        return "end"


# ============================================================================
# 그래프 구축
# ============================================================================

def build_agent_graph(tools):
    """LangGraph StateGraph 구축"""
    
    chatbot_node = create_chatbot_node(tools)
    tool_node = CustomToolNode(tools=tools)
    
    workflow = StateGraph(AgentState)
    
    # 노드 추가
    workflow.add_node("chatbot", chatbot_node)
    workflow.add_node("tools", tool_node)
    
    # 시작점
    workflow.set_entry_point("chatbot")
    
    # 조건부 엣지: tool_calls 여부에 따라 분기
    workflow.add_conditional_edges(
        "chatbot",
        llm_tool_router,
        {
            "tools": "tools",
            "end": END
        }
    )
    
    # tools 실행 후 종료
    workflow.add_edge("tools", END)
    
    return workflow.compile()


# ============================================================================
# 메인 함수
# ============================================================================

def assign_department(
    msg_id: str, 
    top_k: int = 5
) -> int:
    """
    메시지를 분석하여 적절한 부서에 배정 (LangGraph 기반)
    
    Args:
        msg_id: 메시지 ID
        top_k: 검색할 최대 부서 수 (기본값: 5)
        
    Returns:
        0: 일반 채팅
        1: 부서 배정 성공
    """
    # 1. 메시지 내용 조회
    content = get_message_content(msg_id)
    if not content:
        print(f"메시지 ID {msg_id}를 찾을 수 없습니다.")
        return 0
    
    print(f"문의 내용: {content}")
    
    # 2. Tools 정의
    tools = [assign_department_tool]
    
    # 3. 그래프 생성
    agent = build_agent_graph(tools)
    
    # 4. 초기 상태
    initial_state = {
        "messages": [HumanMessage(content=content)],
        "msg_id": msg_id,
        "top_k": top_k
    }
    
    # 5. 에이전트 실행
    result = agent.invoke(initial_state)
    
    # 6. 결과 분석
    messages = result.get("messages", [])
    
    # ToolMessage가 있는지 확인
    for msg in messages:
        if hasattr(msg, "__class__") and msg.__class__.__name__ == "ToolMessage":
            try:
                content = json.loads(msg.content) if isinstance(msg.content, str) else msg.content
                if content.get("success"):
                    print(f"✓ 부서 배정 완료!")
                    return 1
                elif content.get("error"):
                    error_msg = content['error']
                    print(f"✗ 부서 배정 실패: {error_msg}")
                    return 0
            except Exception as e:
                print(f"⚠️  결과 파싱 오류: {e}")
                pass
    
    # 일반 채팅으로 처리됨
    print("일반 채팅으로 처리되었습니다.")
    return 0
