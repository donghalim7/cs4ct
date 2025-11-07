import streamlit as st
from supabase_config import get_supabase_client
from utils import (
    get_departments_by_company,
    get_recent_cs_messages,
    get_most_assigned_cs,
    get_department_cs_queue,
    get_department_stats
)
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 페이지 상태 초기화
if 'page' not in st.session_state:
    st.session_state.page = 1
if 'selected_company' not in st.session_state:
    st.session_state.selected_company = None
if 'selected_dept_id' not in st.session_state:
    st.session_state.selected_dept_id = None

# Supabase 클라이언트 초기화
@st.cache_resource
def init_supabase():
    try:
        return get_supabase_client()
    except Exception as e:
        st.error(f"Supabase 연결 오류: {e}")
        st.info("환경 변수에 SUPABASE_KEY를 설정해주세요.")
        return None

supabase = init_supabase()

# 페이지 1: 회사 선택
def page1_company_selection():
    st.title("CS 관리 시스템")
    st.markdown("---")
    
    st.header("회사 선택")
    
    companies = ["A사", "B사", "C사"]
    
    for company in companies:
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.write(f"### {company}")
        
        with col2:
            if st.button(f"{company} 현황", key=f"btn_{company}"):
                st.session_state.selected_company = company
                st.session_state.page = 2
                st.rerun()
        
        with col3:
            st.write("")  # 빈 공간

# 페이지 2: 회사 대시보드
def page2_company_dashboard():
    if not st.session_state.selected_company:
        st.session_state.page = 1
        st.rerun()
    
    st.title(f"{st.session_state.selected_company} 대시보드")
    
    # 뒤로가기 버튼
    if st.button("← 회사 선택으로 돌아가기"):
        st.session_state.page = 1
        st.session_state.selected_company = None
        st.rerun()
    
    st.markdown("---")
    
    if not supabase:
        st.error("Supabase 연결이 필요합니다.")
        return
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("부서 목록")
        
        # 부서 목록 조회
        departments = get_departments_by_company(supabase, st.session_state.selected_company)
        
        if departments:
            for dept in departments:
                dept_id = dept.get("dept_id")
                dept_name = dept.get("dept_name", "부서명 없음")
                dept_desc = dept.get("dept_desc", "")
                
                with st.container():
                    st.write(f"**{dept_name}**")
                    if dept_desc:
                        st.caption(dept_desc)
                    
                    if st.button(f"{dept_name} 대시보드", key=f"dept_{dept_id}"):
                        st.session_state.selected_dept_id = dept_id
                        st.session_state.page = 3
                        st.rerun()
                    st.markdown("---")
        else:
            st.info("부서 정보가 없습니다.")
    
    with col2:
        # 최근 들어온 CS
        st.subheader("최근 들어온 CS")
        recent_cs = get_recent_cs_messages(supabase, limit=5)
        
        if recent_cs:
            for idx, cs in enumerate(recent_cs, 1):
                msg_data = cs.get("message", {})
                if isinstance(msg_data, list) and msg_data:
                    msg_data = msg_data[0]
                
                content = msg_data.get("content", "내용 없음") if msg_data else "내용 없음"
                msg_id = cs.get("msg_id", "")
                
                with st.container():
                    st.write(f"**{idx}. CS #{msg_id}**")
                    st.caption(content[:100] + "..." if len(content) > 100 else content)
                    st.markdown("---")
        else:
            st.info("최근 CS가 없습니다.")
        
        st.markdown("---")
        
        # CS가 가장 많이 배정된 부서
        st.subheader("CS가 가장 많이 배정된 부서")
        most_assigned = get_most_assigned_cs(supabase, limit=5)
        
        if most_assigned:
            for idx, item in enumerate(most_assigned, 1):
                with st.container():
                    st.write(f"**{idx}. {item['dept_name']}**")
                    st.metric("배정된 CS 수", item['count'])
                    st.markdown("---")
        else:
            st.info("배정 정보가 없습니다.")

# 페이지 3: 부서 상세 대시보드
def page3_department_dashboard():
    if not st.session_state.selected_company or not st.session_state.selected_dept_id:
        st.session_state.page = 2
        st.rerun()
    
    if not supabase:
        st.error("Supabase 연결이 필요합니다.")
        return
    
    # 부서 정보 조회
    dept_info = supabase.table("department").select("*").eq("dept_id", st.session_state.selected_dept_id).execute()
    dept_name = dept_info.data[0].get("dept_name", "부서명 없음") if dept_info.data else "부서명 없음"
    
    st.title(f"{st.session_state.selected_company} - {dept_name} 대시보드")
    
    # 뒤로가기 버튼
    if st.button("← 회사 대시보드로 돌아가기"):
        st.session_state.page = 2
        st.session_state.selected_dept_id = None
        st.rerun()
    
    st.markdown("---")
    
    # 최근 배정된 CS 큐 (가장 위에)
    st.subheader("최근 배정된 CS 큐")
    cs_queue = get_department_cs_queue(supabase, st.session_state.selected_dept_id)
    
    if cs_queue:
        queue_data = []
        for cs in cs_queue:
            msg_data = cs.get("message", {})
            if isinstance(msg_data, list) and msg_data:
                msg_data = msg_data[0]
            
            queue_data.append({
                "CS ID": cs.get("msg_id", ""),
                "내용": msg_data.get("content", "내용 없음")[:100] + "..." if isinstance(msg_data, dict) and len(msg_data.get("content", "")) > 100 else (msg_data.get("content", "내용 없음") if isinstance(msg_data, dict) else "내용 없음"),
                "배정 시간": "최근"  # 실제 배정 시간 필드가 있다면 사용
            })
        
        df_queue = pd.DataFrame(queue_data)
        st.dataframe(df_queue, use_container_width=True, hide_index=True)
    else:
        st.info("배정된 CS가 없습니다.")
    
    st.markdown("---")
    
    # 통계 대시보드
    stats = get_department_stats(supabase, st.session_state.selected_dept_id)
    
    # 상단 KPI 카드
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("총 배정된 CS", stats["total_assigned"])
    
    with col2:
        st.metric("완료된 CS", stats["completed"])
    
    with col3:
        st.metric("완료율", f"{stats['completion_rate']:.1f}%")
    
    st.markdown("---")
    
    # 그래프 영역
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("CS 완료율 추이")
        # 임시 데이터 (실제로는 시간별 데이터가 필요)
        dates = pd.date_range(end=pd.Timestamp.now(), periods=7, freq='D')
        completion_rates = [stats['completion_rate']] * 7  # 임시 데이터
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates,
            y=completion_rates,
            mode='lines+markers',
            name='완료율',
            line=dict(color='#1f77b4', width=2)
        ))
        fig.update_layout(
            title="최근 7일간 CS 완료율",
            xaxis_title="날짜",
            yaxis_title="완료율 (%)",
            height=300
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("팀원별 CS 배정 현황")
        # 임시 데이터 (실제로는 팀원별 배정 데이터가 필요)
        team_members = ["팀원 A", "팀원 B", "팀원 C"]
        assignments = [5, 3, 2]  # 임시 데이터
        
        fig = px.bar(
            x=team_members,
            y=assignments,
            labels={'x': '팀원', 'y': '배정된 CS 수'},
            title="팀원별 배정된 CS 수"
        )
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # 하단 통계 영역
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("CS 문의 카테고리별 통계")
        # 임시 데이터 (실제로는 카테고리별 데이터가 필요)
        categories = ["기술 문의", "버그 리포트", "기능 요청", "기타"]
        counts = [10, 7, 5, 3]
        
        fig = px.pie(
            values=counts,
            names=categories,
            title="카테고리별 CS 분포"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("월별 CS 처리 현황")
        # 임시 데이터
        months = ["1월", "2월", "3월", "4월", "5월"]
        processed = [15, 20, 18, 22, 25]
        
        fig = px.bar(
            x=months,
            y=processed,
            labels={'x': '월', 'y': '처리된 CS 수'},
            title="월별 처리 현황"
        )
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)

# 메인 앱 라우팅
def main():
    st.set_page_config(
        page_title="CS 관리 시스템",
        page_icon="📊",
        layout="wide"
    )
    
    if st.session_state.page == 1:
        page1_company_selection()
    elif st.session_state.page == 2:
        page2_company_dashboard()
    elif st.session_state.page == 3:
        page3_department_dashboard()

if __name__ == "__main__":
    main()


