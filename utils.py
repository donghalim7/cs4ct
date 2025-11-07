import pandas as pd
from datetime import datetime, timedelta
import requests
import hashlib

server_url = "http://13.209.68.160:8000"

def api_department():
    return f"{server_url}/department/all"

def api_assigned_message_by_department(department_id: int):
    return f"{server_url}/msg/all?d_id={department_id}"

def api_assigned_message():
    return f"{server_url}/msg/all"

def get_departments_by_company(company_name: str = None):
    """회사별 부서 목록 조회 (서버 API 사용) - dept_desc는 제외, Supabase에서 가져옴"""
    try:
        response = requests.get(api_department(), timeout=(5, 600))
        response.encoding = 'utf-8'
        response.raise_for_status()
        data = response.json()
        
        # 응답 형식: {'data': [{"department_id": int, "name": string}, ...], "status": string}
        if not isinstance(data, dict) or "data" not in data:
            return []
        
        dept_list = data["data"]
        
        # 필드명 변환: department_id -> dept_id, name -> dept_name
        # dept_desc는 Supabase에서 가져올 예정이므로 여기서는 포함하지 않음
        normalized_list = []
        for dept in dept_list:
            normalized = {
                "dept_id": dept.get("department_id"),
                "dept_name": dept.get("name", ""),
            }
            if normalized["dept_id"] is not None:
                normalized_list.append(normalized)
        
        return normalized_list
    except Exception as e:
        print(f"부서 조회 오류: {e}")
        import traceback
        traceback.print_exc()
        return []

def get_recent_cs_messages(limit: int = 10):
    """최근 CS 메시지 조회 (서버 API 사용)"""
    try:
        response = requests.get(api_assigned_message(), timeout=(5, 600))
        response.encoding = 'utf-8'
        response.raise_for_status()
        data = response.json()
        
        # 응답 형식: {'data': [{'content': '...', 'timestamp': '...'}, ...], 'status': 'success'}
        if not isinstance(data, dict) or "data" not in data:
            return []
        
        messages = data["data"]
        
        # timestamp 기준으로 정렬 (최신순)
        def get_timestamp(item):
            timestamp = item.get("timestamp", "")
            if timestamp:
                try:
                    # ISO 형식 파싱 (Z 또는 +00:00 처리)
                    timestamp_str = timestamp.replace('Z', '+00:00') if isinstance(timestamp, str) else str(timestamp)
                    return datetime.fromisoformat(timestamp_str)
                except Exception as e:
                    print(f"timestamp 파싱 오류: {e}, timestamp: {timestamp}")
                    return datetime.min
            return datetime.min
        
        messages.sort(key=get_timestamp, reverse=True)
        
        # Supabase 형식과 호환되도록 변환 (msg_id는 content+timestamp 해시로 생성)
        processed_data = []
        seen_contents = set()  # 중복 제거용
        
        for msg in messages[:limit * 2]:  # 중복 제거를 위해 더 많이 가져옴
            content = msg.get("content", "")
            timestamp = msg.get("timestamp", "")
            
            # 중복 제거 (동일한 content는 제외)
            content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()[:8]
            if content_hash in seen_contents:
                continue
            seen_contents.add(content_hash)
            
            # msg_id 생성 (content + timestamp 기반 해시)
            msg_id_str = f"{content}{timestamp}"
            msg_id = int(hashlib.md5(msg_id_str.encode('utf-8')).hexdigest()[:13], 16)
            
            # Supabase 형식과 호환되도록 변환
            processed_item = {
                "msg_id": msg_id,
                "dept_id": None,  # 서버 API에는 dept_id가 없음
                "message": {
                    "msg_id": msg_id,
                    "content": content,
                    "timestamp": timestamp
                }
            }
            processed_data.append(processed_item)
            
            if len(processed_data) >= limit:
                break
        
        return processed_data
    except Exception as e:
        print(f"최근 CS 조회 오류: {e}")
        import traceback
        traceback.print_exc()
        return []

def get_most_assigned_cs(limit: int = 5):
    """가장 많이 배정된 CS 조회 (부서별) - 서버 API 사용"""
    try:
        # 부서 목록 조회
        dept_response = requests.get(api_department(), timeout=10)
        dept_response.encoding = 'utf-8'
        dept_response.raise_for_status()
        dept_data = dept_response.json()
        
        if not isinstance(dept_data, dict) or "data" not in dept_data:
            return []
        
        dept_list = dept_data["data"]
        
        # 각 부서별로 메시지 개수 조회
        dept_counts = []
        for dept in dept_list:
            dept_id = dept.get("department_id")
            if dept_id is None:
                continue
            
            try:
                # 부서별 메시지 조회
                msg_response = requests.get(api_assigned_message_by_department(dept_id), timeout=(5, 600))
                msg_response.encoding = 'utf-8'
                msg_response.raise_for_status()
                msg_data = msg_response.json()
                
                if isinstance(msg_data, dict) and "data" in msg_data:
                    count = len(msg_data["data"])
                    if count > 0:
                        dept_counts.append({
                            "dept_id": dept_id,
                            "dept_name": dept.get("name", ""),
                            "count": count
                        })
            except Exception as e:
                print(f"부서 {dept_id} 메시지 조회 오류: {e}")
                continue
        
        # count 기준으로 정렬
        dept_counts.sort(key=lambda x: x["count"], reverse=True)
        
        return dept_counts[:limit]
    except Exception as e:
        print(f"많이 배정된 CS 조회 오류: {e}")
        import traceback
        traceback.print_exc()
        return []

def get_department_cs_queue(dept_id: int):
    """특정 부서에 배정된 최근 CS 큐 조회 (서버 API 사용)"""
    try:
        response = requests.get(api_assigned_message_by_department(dept_id), timeout=(5, 600))
        response.encoding = 'utf-8'
        response.raise_for_status()
        data = response.json()
        
        # 응답 형식: {'data': [{'content': '...', 'timestamp': '...'}, ...], 'status': 'success'}
        if not isinstance(data, dict) or "data" not in data:
            return []
        
        messages = data["data"]
        
        # timestamp 기준으로 정렬 (최신순)
        def get_timestamp(item):
            timestamp = item.get("timestamp", "")
            if timestamp:
                try:
                    # ISO 형식 파싱 (Z 또는 +00:00 처리)
                    timestamp_str = timestamp.replace('Z', '+00:00') if isinstance(timestamp, str) else str(timestamp)
                    return datetime.fromisoformat(timestamp_str)
                except Exception as e:
                    print(f"timestamp 파싱 오류: {e}, timestamp: {timestamp}")
                    return datetime.min
            return datetime.min
        
        messages.sort(key=get_timestamp, reverse=True)
        
        # Supabase 형식과 호환되도록 변환
        processed_data = []
        for msg in messages:
            content = msg.get("content", "")
            timestamp = msg.get("timestamp", "")
            
            # msg_id 생성 (content + timestamp 기반 해시)
            msg_id_str = f"{content}{timestamp}"
            msg_id = int(hashlib.md5(msg_id_str.encode('utf-8')).hexdigest()[:13], 16)
            
            processed_item = {
                "msg_id": msg_id,
                "dept_id": dept_id,
                "message": {
                    "msg_id": msg_id,
                    "content": content,
                    "timestamp": timestamp
                }
            }
            processed_data.append(processed_item)
        
        return processed_data
    except Exception as e:
        print(f"부서 CS 큐 조회 오류: {e}")
        import traceback
        traceback.print_exc()
        return []

def get_department_stats(dept_id: int):
    """부서별 통계 조회 (서버 API 사용)"""
    try:
        # 해당 부서에 배정된 메시지 조회
        response = requests.get(api_assigned_message_by_department(dept_id), timeout=(5, 600))
        response.encoding = 'utf-8'
        response.raise_for_status()
        data = response.json()
        
        if not isinstance(data, dict) or "data" not in data:
            return {
                "total_assigned": 0,
                "completed": 0,
                "completion_rate": 0
            }
        
        messages = data["data"]
        total_assigned = len(messages)
        
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
        import traceback
        traceback.print_exc()
        return {
            "total_assigned": 0,
            "completed": 0,
            "completion_rate": 0
        }

