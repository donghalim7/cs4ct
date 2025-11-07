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
from datetime import datetime

# 커스텀 CSS 스타일
def load_custom_css():
    st.markdown("""
    <style>
    /* 전체 테마 설정 */
    :root {
        --mint: #4ECDC4;
        --purple: #9B59B6;
        --black: #1a1a1a;
        --white: #ffffff;
        --light-gray: #f5f5f5;
        --dark-gray: #2d2d2d;
    }
    
    /* 메인 컨테이너 스타일 */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* 타이틀 스타일 */
    h1 {
        color: var(--black) !important;
        font-weight: 700 !important;
        margin-bottom: 1.5rem !important;
        background: linear-gradient(135deg, var(--purple) 0%, var(--mint) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    h2 {
        color: var(--black) !important;
        font-weight: 600 !important;
        margin-top: 2rem !important;
        margin-bottom: 1rem !important;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid var(--mint);
    }
    
    h3 {
        color: var(--dark-gray) !important;
        font-weight: 600 !important;
    }
    
    /* 카드 스타일 */
    .custom-card {
        background: var(--white);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        border-left: 4px solid var(--mint);
        transition: transform 0.2s, box-shadow 0.2s;
    }
    
    .custom-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(78, 205, 196, 0.2);
    }
    
    .custom-card-purple {
        border-left-color: var(--purple);
    }
    
    /* 버튼 스타일 */
    .stButton > button {
        background: linear-gradient(135deg, var(--mint) 0%, #3AB5AE 100%);
        color: var(--white);
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s;
        box-shadow: 0 2px 6px rgba(78, 205, 196, 0.3);
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #3AB5AE 0%, var(--mint) 100%);
        box-shadow: 0 4px 12px rgba(78, 205, 196, 0.4);
        transform: translateY(-1px);
    }
    
    /* 메트릭 카드 스타일 */
    [data-testid="stMetricValue"] {
        font-size: 2rem !important;
        font-weight: 700 !important;
        background: linear-gradient(135deg, var(--purple) 0%, var(--mint) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    [data-testid="stMetricLabel"] {
        color: var(--dark-gray) !important;
        font-weight: 500 !important;
    }
    
    /* 구분선 스타일 */
    hr {
        border: none;
        height: 2px;
        background: linear-gradient(90deg, transparent, var(--mint), transparent);
        margin: 2rem 0;
    }
    
    /* 데이터프레임 스타일 */
    .dataframe {
        border-radius: 8px;
        overflow: hidden;
    }
    
    /* 인포 박스 스타일 */
    .stInfo {
        background: linear-gradient(135deg, rgba(78, 205, 196, 0.1) 0%, rgba(155, 89, 182, 0.1) 100%);
        border-left: 4px solid var(--mint);
        border-radius: 8px;
    }
    
    /* CS 아이템 스타일 */
    .cs-item {
        background: var(--white);
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 0.75rem;
        border-left: 3px solid var(--mint);
        box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
        transition: all 0.2s;
    }
    
    .cs-item:hover {
        box-shadow: 0 3px 8px rgba(78, 205, 196, 0.15);
        transform: translateX(4px);
    }
    
    /* 부서 카드 스타일 */
    .dept-card {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.9) 0%, rgba(248, 250, 252, 0.9) 100%);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        border: 1px solid rgba(78, 205, 196, 0.2);
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
        transition: all 0.3s;
    }
    
    .dept-card:hover {
        border-color: var(--mint);
        box-shadow: 0 4px 16px rgba(78, 205, 196, 0.15);
        transform: translateY(-2px);
    }
    
    /* 스크롤바 스타일 */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--light-gray);
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, var(--mint) 0%, var(--purple) 100%);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, var(--purple) 0%, var(--mint) 100%);
    }
    
    /* 검색 입력창 스타일 */
    .stTextInput > div > div > input {
        border-radius: 8px;
        border: 2px solid rgba(78, 205, 196, 0.3);
        padding: 0.5rem 1rem;
        transition: all 0.3s;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: var(--mint);
        box-shadow: 0 0 0 3px rgba(78, 205, 196, 0.1);
    }
    
    /* 부서 카드 가로 레이아웃 개선 */
    .dept-card-horizontal {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)

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
    st.markdown("""
    <div style='text-align: center; padding: 2rem 0;'>
        <h1 style='font-size: 3rem; margin-bottom: 0.5rem;'>📊 CS 관리 시스템</h1>
        <p style='color: #666; font-size: 1.1rem;'>고객 서비스를 효율적으로 관리하세요</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("### 🏢 회사 선택")
    st.markdown("<br>", unsafe_allow_html=True)
    
    companies = ["차널톡", "마신사", "솜성"]
    
    # 회사 카드 그리드
    cols = st.columns(3)
    for idx, company in enumerate(companies):
        with cols[idx]:
            st.markdown(f"""
            <div class='dept-card' style='text-align: center;'>
                <h3 style='margin-bottom: 1rem;'>{company}</h3>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button(f"📈 {company} 현황 보기", key=f"btn_{company}", use_container_width=True):
                st.session_state.selected_company = company
                st.session_state.page = 2
                st.rerun()

# 페이지 2: 회사 대시보드
def page2_company_dashboard():
    if not st.session_state.selected_company:
        st.session_state.page = 1
        st.rerun()
    
    # 헤더 영역
    col_header1, col_header2 = st.columns([4, 1])
    with col_header1:
        st.markdown(f"<h1>🏢 {st.session_state.selected_company} 대시보드</h1>", unsafe_allow_html=True)
    with col_header2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("← 돌아가기", use_container_width=True):
            st.session_state.page = 1
            st.session_state.selected_company = None
            st.rerun()
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### 📁 부서 목록")
        st.markdown("<br>", unsafe_allow_html=True)
        
        # 검색 기능 추가
        if 'dept_search' not in st.session_state:
            st.session_state.dept_search = ""
        
        search_query = st.text_input(
            "🔍 부서 검색",
            value=st.session_state.dept_search,
            placeholder="부서명을 입력하세요...",
            key="dept_search_input"
        )
        st.session_state.dept_search = search_query
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # 부서 목록 조회
        departments = get_departments_by_company()
        
        # 검색어로 필터링
        if search_query:
            departments = [
                dept for dept in departments 
                if search_query.lower() in dept.get("name", "").lower()
            ]
        
        if departments:
            for dept in departments:
                dept_id = dept.get("department_id")
                dept_name = dept.get("name", "부서명 없음")
                dept_desc = dept.get("dept_desc", "")
                
                # 가로 레이아웃: 왼쪽에 부서 정보, 오른쪽에 버튼
                col_info, col_btn = st.columns([3.5, 1])
                
                with col_info:
                    st.markdown(f"""
                    <div class='dept-card' style='margin-bottom: 0; padding: 1rem; height: 100%; display: flex; flex-direction: column; justify-content: center;'>
                        <h3 style='margin-bottom: 0.5rem; margin-top: 0;'>{dept_name}</h3>
                        <p style='color: #666; margin-bottom: 0; font-size: 0.9rem;'>{dept_desc if dept_desc else '부서 설명이 없습니다.'}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col_btn:
                    st.markdown("<div style='display: flex; align-items: center; height: 100%; padding-left: 0.5rem;'>", unsafe_allow_html=True)
                    if st.button(f"📊 대시보드", key=f"dept_{dept_id}", use_container_width=True):
                        st.session_state.selected_dept_id = dept_id
                        st.session_state.page = 3
                        st.session_state.selected_dept_name = dept_name
                        st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
        else:
            if search_query:
                st.info(f"'{search_query}'에 해당하는 부서를 찾을 수 없습니다.")
            else:
                st.info("부서 정보가 없습니다.")
    
    with col2:
        # 최근 들어온 CS
        st.markdown("### 💬 최근 들어온 CS")
        st.markdown("<br>", unsafe_allow_html=True)
        recent_cs = get_recent_cs_messages(supabase, limit=5)
        
        if recent_cs:
            for idx, cs in enumerate(recent_cs, 1):
                msg_data = cs.get("message", {})
                if isinstance(msg_data, list) and msg_data:
                    msg_data = msg_data[0]
                
                content = msg_data.get("content", "내용 없음") if msg_data else "내용 없음"
                msg_id = cs.get("msg_id", "")
                display_content = content[:80] + "..." if len(content) > 80 else content
                
                st.markdown(f"""
                <div class='cs-item'>
                    <strong style='color: #9B59B6; font-size: 1.1rem;'>#{idx} CS #{msg_id}</strong>
                    <p style='color: #555; margin-top: 0.5rem; margin-bottom: 0;'>{display_content}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("최근 CS가 없습니다.")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # CS가 가장 많이 배정된 부서
        st.markdown("### 🏆 CS가 가장 많이 배정된 부서")
        st.markdown("<br>", unsafe_allow_html=True)
        most_assigned = get_most_assigned_cs(supabase, limit=5)
        
        if most_assigned:
            for idx, item in enumerate(most_assigned, 1):
                st.markdown(f"""
                <div class='cs-item' style='border-left-color: #9B59B6;'>
                    <strong style='color: #1a1a1a; font-size: 1rem;'>#{idx} {item['dept_name']}</strong>
                    <div style='margin-top: 0.5rem;'>
                        <span style='background: linear-gradient(135deg, #9B59B6 0%, #4ECDC4 100%); 
                                     color: white; padding: 0.25rem 0.75rem; border-radius: 20px; 
                                     font-size: 0.9rem; font-weight: 600;'>
                            {item['count']}건 배정
                        </span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("배정 정보가 없습니다.")

# 페이지 3: 부서 상세 대시보드
def page3_department_dashboard():
    if not st.session_state.selected_company or not st.session_state.selected_dept_id:
        st.session_state.page = 2
        st.rerun()
    
    # 부서 정보 조회
    dept_info = get_department_cs_queue(supabase, st.session_state.selected_dept_id)
    dept_name = st.session_state.selected_dept_name
    
    # 헤더 영역
    col_header1, col_header2 = st.columns([4, 1])
    with col_header1:
        st.markdown(f"<h1>📊 {st.session_state.selected_company} - {dept_name} 대시보드</h1>", unsafe_allow_html=True)
    with col_header2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("← 돌아가기", use_container_width=True):
            st.session_state.page = 2
            st.session_state.selected_dept_id = None
            st.session_state.selected_dept_name = None
            st.rerun()
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 최근 배정된 CS 큐 (가장 위에)
    st.markdown("### 📋 최근 배정된 CS 큐")
    st.markdown("<br>", unsafe_allow_html=True)
    cs_queue = get_department_cs_queue(supabase, st.session_state.selected_dept_id)
    
    if cs_queue:
        queue_data = []
        for cs in cs_queue:
            msg_data = cs.get("message", {})
            if isinstance(msg_data, list) and msg_data:
                msg_data = msg_data[0]
            
            # timestamp 처리
            timestamp = msg_data.get("timestamp", "") if isinstance(msg_data, dict) else ""
            if timestamp:
                try:
                    # ISO 형식의 timestamp를 파싱
                    if isinstance(timestamp, str):
                        # Z를 +00:00으로 변환하여 파싱
                        timestamp_str = timestamp.replace('Z', '+00:00')
                        dt = datetime.fromisoformat(timestamp_str)
                        # 타임존 정보가 있으면 로컬 시간으로 변환
                        if dt.tzinfo:
                            dt = dt.astimezone()
                        formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        formatted_time = str(timestamp)
                except Exception as e:
                    # 파싱 실패 시 원본 문자열 반환
                    formatted_time = str(timestamp) if timestamp else "시간 정보 없음"
            else:
                formatted_time = "시간 정보 없음"
            
            queue_data.append({
                "CS ID": cs.get("msg_id", ""),
                "내용": msg_data.get("content", "내용 없음")[:100] + "..." if isinstance(msg_data, dict) and len(msg_data.get("content", "")) > 100 else (msg_data.get("content", "내용 없음") if isinstance(msg_data, dict) else "내용 없음"),
                "배정 시간": formatted_time
            })
        
        df_queue = pd.DataFrame(queue_data)
        st.dataframe(
            df_queue, 
            use_container_width=True, 
            hide_index=True,
            height=min(len(queue_data) * 50 + 50, 400)
        )
    else:
        st.info("배정된 CS가 없습니다.")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 통계 대시보드
    stats = get_department_stats(supabase, st.session_state.selected_dept_id)
    
    # 상단 KPI 카드
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class='custom-card' style='text-align: center;'>
            <div style='font-size: 0.9rem; color: #666; margin-bottom: 0.5rem;'>총 배정된 CS</div>
        </div>
        """, unsafe_allow_html=True)
        st.metric("", stats["total_assigned"], delta=None)
    
    with col2:
        st.markdown("""
        <div class='custom-card custom-card-purple' style='text-align: center;'>
            <div style='font-size: 0.9rem; color: #666; margin-bottom: 0.5rem;'>완료된 CS</div>
        </div>
        """, unsafe_allow_html=True)
        st.metric("", stats["completed"], delta=None)
    
    with col3:
        st.markdown("""
        <div class='custom-card' style='text-align: center;'>
            <div style='font-size: 0.9rem; color: #666; margin-bottom: 0.5rem;'>완료율</div>
        </div>
        """, unsafe_allow_html=True)
        st.metric("", f"{stats['completion_rate']:.1f}%", delta=None)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 그래프 영역
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📈 CS 완료율 추이")
        # 임시 데이터 (실제로는 시간별 데이터가 필요)
        dates = pd.date_range(end=pd.Timestamp.now(), periods=7, freq='D')
        completion_rates = [stats['completion_rate']] * 7  # 임시 데이터
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates,
            y=completion_rates,
            mode='lines+markers',
            name='완료율',
            line=dict(color='#4ECDC4', width=3),
            marker=dict(size=8, color='#9B59B6'),
            fill='tonexty',
            fillcolor='rgba(78, 205, 196, 0.1)'
        ))
        fig.update_layout(
            title="최근 7일간 CS 완료율",
            xaxis_title="날짜",
            yaxis_title="완료율 (%)",
            height=350,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#1a1a1a')
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### 👥 팀원별 CS 배정 현황")
        # 임시 데이터 (실제로는 팀원별 배정 데이터가 필요)
        team_members = ["팀원 A", "팀원 B", "팀원 C"]
        assignments = [5, 3, 2]  # 임시 데이터
        
        fig = px.bar(
            x=team_members,
            y=assignments,
            labels={'x': '팀원', 'y': '배정된 CS 수'},
            title="팀원별 배정된 CS 수",
            color=assignments,
            color_continuous_scale=['#4ECDC4', '#9B59B6']
        )
        fig.update_layout(
            height=350,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#1a1a1a'),
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 하단 통계 영역
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🎯 CS 문의 카테고리별 통계")
        # 임시 데이터 (실제로는 카테고리별 데이터가 필요)
        categories = ["기술 문의", "버그 리포트", "기능 요청", "기타"]
        counts = [10, 7, 5, 3]
        
        colors = ['#4ECDC4', '#9B59B6', '#3AB5AE', '#7D3C98']
        fig = px.pie(
            values=counts,
            names=categories,
            title="카테고리별 CS 분포",
            color_discrete_sequence=colors
        )
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#1a1a1a')
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### 📅 월별 CS 처리 현황")
        # 임시 데이터
        months = ["1월", "2월", "3월", "4월", "5월"]
        processed = [15, 20, 18, 22, 25]
        
        fig = px.bar(
            x=months,
            y=processed,
            labels={'x': '월', 'y': '처리된 CS 수'},
            title="월별 처리 현황",
            color=processed,
            color_continuous_scale=['#9B59B6', '#4ECDC4']
        )
        fig.update_layout(
            height=350,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#1a1a1a'),
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)

# 메인 앱 라우팅
def main():
    st.set_page_config(
        page_title="CS 관리 시스템",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # 커스텀 CSS 로드
    load_custom_css()
    
    if st.session_state.page == 1:
        page1_company_selection()
    elif st.session_state.page == 2:
        page2_company_dashboard()
    elif st.session_state.page == 3:
        page3_department_dashboard()

if __name__ == "__main__":
    main()


