# ============================================================================
# Stage 1: 빌드 스테이지 (컴파일 도구 포함)
# ============================================================================
FROM python:3.12-slim AS builder

WORKDIR /app

# 빌드에 필요한 도구만 설치
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# requirements.txt 복사 및 패키지 설치
# 이 레이어는 requirements.txt가 변경되지 않는 한 캐시됨 (가장 큰 시간 절약)
COPY requirements.txt .

# torch를 CPU 전용으로 먼저 설치 (CUDA 버전 설치 방지, 디스크 공간 절약)
RUN pip install --no-cache-dir --user --index-url https://download.pytorch.org/whl/cpu torch>=2.0.0

# 나머지 패키지 설치 (torch가 이미 설치되어 있으므로 CUDA 버전을 설치하지 않음)
RUN pip install --no-cache-dir --user -r requirements.txt

# ============================================================================
# Stage 2: 런타임 스테이지 (최소한의 이미지)
# ============================================================================
FROM python:3.12-slim

WORKDIR /app

# 빌드 스테이지에서 설치한 패키지만 복사 (gcc 등 빌드 도구 제외)
COPY --from=builder /root/.local /root/.local

# PATH에 사용자 로컬 bin 추가
ENV PATH=/root/.local/bin:$PATH

# 애플리케이션 코드를 별도 레이어로 분리 (캐싱 최적화)
# agent.py는 덜 자주 변경되므로 먼저 복사
COPY agent.py .
# app.py는 자주 변경되므로 마지막에 복사
COPY app.py .

# 포트 노출
EXPOSE 8000

# 환경 변수 설정
ENV FLASK_APP=app.py
ENV PYTHONUNBUFFERED=1

# Flask 앱 실행
CMD ["python", "app.py"]

