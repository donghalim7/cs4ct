import requests
from datetime import datetime, timedelta

server_url = "http://15.164.229.202:8000"

def api_department ():
    return f"{server_url}/department/all"

def api_assigned_message_by_department(department_id: int):
    return f"{server_url}/msg/all?d_id={department_id}"

def api_assigned_message():
    return f"{server_url}/msg/all"

def get_department_cs_queue(dept_id: int):
    """특정 부서에 배정된 최근 CS 큐 조회"""
    try:
        response = requests.get(api_assigned_message_by_department(dept_id))
        response.raise_for_status()
        response = response.json()
        
        return response
    except Exception as e2:
        print(f"부서 CS 큐 조회 오류: {e2}")
        return []

print(get_department_cs_queue(24))