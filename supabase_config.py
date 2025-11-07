import os
from pathlib import Path
from supabase import create_client, Client
from dotenv import load_dotenv

# .env 파일 경로 찾기 (현재 파일 기준으로 프로젝트 루트 찾기)
BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / ".env"

# .env 파일이 존재하는지 확인하고 로드
if ENV_FILE.exists():
    load_dotenv(dotenv_path=ENV_FILE, override=True)
else:
    # 파일이 없으면 현재 작업 디렉토리에서도 시도
    load_dotenv(override=True)

# Supabase 설정
SUPABASE_URL = f"https://ewftdvslhefeipjpkvnf.supabase.co"
# 환경 변수에서 키를 읽거나, 없으면 .env 파일에서 직접 읽기
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
if not SUPABASE_KEY:
    # .env 파일에서 직접 읽기 시도
    try:
        if ENV_FILE.exists():
            with open(ENV_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('SUPABASE_KEY='):
                        SUPABASE_KEY = line.split('=', 1)[1].strip()
                        break
    except Exception as e:
        print(f"환경 변수 로드 오류: {e}")

# 하드코딩된 키 (임시, .env 파일이 제대로 읽히지 않을 때 사용)
if not SUPABASE_KEY:
    SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV3ZnRkdnNsaGVmZWlwanBrdm5mIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjI1MTQ4MDQsImV4cCI6MjA3ODA5MDgwNH0.2ya2XRvzGQZHRIvmKio7K6oJPw-e0axKrRHzlpdnfeA"
# 디버깅: 키가 로드되었는지 확인 (프로덕션에서는 제거 가능)
if not SUPABASE_KEY:
    print(f"경고: SUPABASE_KEY를 찾을 수 없습니다.")
    print(f"ENV_FILE 경로: {ENV_FILE}")
    print(f"파일 존재 여부: {ENV_FILE.exists()}")
    print(f"현재 작업 디렉토리: {os.getcwd()}")

def get_supabase_client() -> Client:
    """Supabase 클라이언트 생성"""
    if not SUPABASE_KEY:
        raise ValueError("SUPABASE_KEY 환경 변수가 설정되지 않았습니다.")
    return create_client(SUPABASE_URL, SUPABASE_KEY)


