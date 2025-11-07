from supabase import Client
import pandas as pd
from datetime import datetime, timedelta

import requests

server_url = "http://15.164.229.202:8000"

def api_department ():
    return f"{server_url}/department/all"

def api_assigned_message_by_department(department_id: int):
    return f"{server_url}/msg/all?d_id={department_id}"

def api_assigned_message():
    return f"{server_url}/msg/all"

def get_departments_by_company():
    """회사별 부서 목록 조회"""
    try:
        response = requests.get(api_department())
        response.raise_for_status()
        response = response.json()
        # 실제로는 company_id나 company_name 필드가 있을 것으로 예상되지만,
        # 현재 스키마에는 없으므로 모든 부서를 반환
        # 추후 company 필드가 추가되면 필터링 가능
        return response["data"]
    except Exception as e:
        print(f"부서 조회 오류: {e}")
        return []

# def get_recent_cs_messages(limit: int = 10):
#     """최근 CS 메시지 조회"""
#     try:
#         # assigned_message와 message를 조인하여 최근 메시지 조회
#         response = requests.get(api_assigned_message())
#         response.raise_for_status()
#         response = response.json()
#         sorted_data = sorted(response, key=lambda x: x["timestamp"])
        
#         # response = supabase.table("assigned_message").select(
#         #     "msg_id, dept_id, message(msg_id, content)"
#         # ).order("msg_id", desc=True).limit(limit).execute()
        
#         return sorted_data[:limit]
#     except Exception as e2:
#         print(f"최근 CS 조회 오류: {e2}")
#         return []

# def get_most_assigned_cs(limit: int = 5):
#     """가장 많이 배정된 CS 조회 (부서별)"""
#     try:
#         # assigned_message에서 dept_id별로 그룹화하여 카운트
#         response = supabase.table("assigned_message").select("dept_id").execute()
        
#         if not response.data:
#             return []
        
#         # pandas로 그룹화
#         df = pd.DataFrame(response.data)
#         dept_counts = df['dept_id'].value_counts().head(limit)
        
#         # 부서 정보와 함께 반환
#         result = []
#         for dept_id, count in dept_counts.items():
#             dept_info = supabase.table("department").select("*").eq("dept_id", dept_id).execute()
#             if dept_info.data:
#                 result.append({
#                     "dept_id": dept_id,
#                     "dept_name": dept_info.data[0].get("dept_name", ""),
#                     "count": int(count)
#                 })
        
#         return result
#     except Exception as e:
#         print(f"많이 배정된 CS 조회 오류: {e}")
#         return []

def get_recent_cs_messages(supabase: Client, limit: int = 10):
    """최근 CS 메시지 조회"""
    try:
        # assigned_message와 message를 조인하여 최근 메시지 조회
        response = supabase.table("assigned_message").select(
            "msg_id, dept_id, message(msg_id, content)"
        ).order("msg_id", desc=True).limit(limit * 2).execute()  # 중복 제거를 위해 더 많이 가져옴
        
        # msg_id 기준으로 중복 제거
        seen_msg_ids = set()
        unique_data = []
        for item in response.data:
            msg_id = item.get("msg_id")
            if msg_id not in seen_msg_ids:
                seen_msg_ids.add(msg_id)
                unique_data.append(item)
                if len(unique_data) >= limit:
                    break
        
        return unique_data
    except Exception as e:
        # order 메서드가 지원되지 않는 경우 대체 방법
        try:
            response = supabase.table("assigned_message").select(
                "msg_id, dept_id, message(msg_id, content)"
            ).limit(limit * 3).execute()  # 중복 제거를 위해 더 많이 가져옴
            # 데이터를 정렬
            if response.data:
                response.data.sort(key=lambda x: x.get("msg_id", 0), reverse=True)
                # msg_id 기준으로 중복 제거
                seen_msg_ids = set()
                unique_data = []
                for item in response.data:
                    msg_id = item.get("msg_id")
                    if msg_id not in seen_msg_ids:
                        seen_msg_ids.add(msg_id)
                        unique_data.append(item)
                        if len(unique_data) >= limit:
                            break
                return unique_data
            return response.data
        except Exception as e2:
            print(f"최근 CS 조회 오류: {e2}")
            return []

def get_most_assigned_cs(supabase: Client, limit: int = 5):
    """가장 많이 배정된 CS 조회 (부서별)"""
    try:
        # assigned_message에서 dept_id별로 그룹화하여 카운트
        response = supabase.table("assigned_message").select("dept_id").execute()
        
        if not response.data:
            return []
        
        # pandas로 그룹화
        df = pd.DataFrame(response.data)
        dept_counts = df['dept_id'].value_counts().head(limit)
        
        # 부서 정보와 함께 반환
        result = []
        for dept_id, count in dept_counts.items():
            dept_info = supabase.table("department").select("*").eq("dept_id", dept_id).execute()
            if dept_info.data:
                result.append({
                    "dept_id": dept_id,
                    "dept_name": dept_info.data[0].get("dept_name", ""),
                    "count": int(count)
                })
        
        return result
    except Exception as e:
        print(f"많이 배정된 CS 조회 오류: {e}")
        return []

# def get_department_cs_queue(dept_id: int):
#     """특정 부서에 배정된 최근 CS 큐 조회"""
#     try:
#         response = requests.get(api_assigned_message_by_department(dept_id))
#         response.raise_for_status()
#         response = response.json()
        
#         return response
#     except Exception as e2:
#         print(f"부서 CS 큐 조회 오류: {e2}")
#         return []

def get_department_cs_queue(supabase: Client, dept_id: int):
    """특정 부서에 배정된 최근 CS 큐 조회"""
    try:
        response = supabase.table("assigned_message").select(
            "msg_id, dept_id, message(msg_id, content, timestamp)"
        ).eq("dept_id", dept_id).execute()
        
        # timestamp 기준으로 정렬 (최신순)
        if response.data:
            def get_timestamp(item):
                msg_data = item.get("message", {})
                if isinstance(msg_data, list) and msg_data:
                    msg_data = msg_data[0]
                timestamp = msg_data.get("timestamp", "") if isinstance(msg_data, dict) else ""
                if timestamp:
                    try:
                        timestamp_str = timestamp.replace('Z', '+00:00')
                        return datetime.fromisoformat(timestamp_str)
                    except:
                        return datetime.min
                return datetime.min
            
            response.data.sort(key=get_timestamp, reverse=True)
        
        return response.data
    except Exception as e:
        print(f"부서 CS 큐 조회 오류: {e}")
        return []

def get_department_stats(supabase: Client, dept_id: int):
    """부서별 통계 조회"""
    try:
        # 해당 부서에 배정된 메시지 수
        assigned = supabase.table("assigned_message").select("*").eq("dept_id", dept_id).execute()
        total_assigned = len(assigned.data) if assigned.data else 0
        
        # 완료된 메시지 수 (완료 상태를 나타내는 필드가 있다고 가정)
        # 현재 스키마에는 완료 상태 필드가 없으므로, 임시로 전체를 미완료로 처리
        completed = 0  # 추후 완료 상태 필드 추가 시 수정 필요
        
        completion_rate = (completed / total_assigned * 100) if total_assigned > 0 else 0
        
        return {
            "total_assigned": total_assigned,
            "completed": completed,
            "completion_rate": completion_rate
        }
    except Exception as e:
        print(f"부서 통계 조회 오류: {e}")
        return {
            "total_assigned": 0,
            "completed": 0,
            "completion_rate": 0
        }

