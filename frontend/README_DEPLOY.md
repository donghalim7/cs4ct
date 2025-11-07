# Streamlit Cloud 배포 가이드

## ⚠️ Netlify는 Streamlit 앱에 적합하지 않습니다

Netlify는 **정적 사이트**와 **서버리스 함수**를 위한 플랫폼입니다. 
Streamlit은 **Python 서버 애플리케이션**이므로 Netlify에서 직접 실행할 수 없습니다.

## ✅ 권장: Streamlit Cloud 사용

Streamlit Cloud는 Streamlit 앱을 무료로 호스팅해주는 공식 플랫폼입니다.

### 1. GitHub에 코드 푸시

```bash
git add .
git commit -m "Prepare for Streamlit Cloud deployment"
git push origin main
```

### 2. Streamlit Cloud에 배포

1. **Streamlit Cloud 접속**
   - https://share.streamlit.io 접속
   - GitHub 계정으로 로그인 (처음이면 GitHub 연결 필요)

2. **앱 배포**
   - "New app" 클릭
   - Repository: `channelio-hackerton` 선택
   - Branch: `main` (또는 사용하는 브랜치)
   - Main file path: `app.py`
   - "Deploy!" 클릭

3. **환경 변수 설정 (Secrets)**
   - 배포 후 앱 대시보드에서 "Settings" → "Secrets" 클릭
   - 또는 앱 URL에서 "☰" 메뉴 → "Settings" → "Secrets"

### 3. Secrets 설정

Streamlit Cloud의 Secrets에 다음을 추가:

```toml
SERVER_URL = "http://54.180.121.208:8000"
SUPABASE_KEY = "your_supabase_key_here"
```

**설정 방법:**
1. Streamlit Cloud 대시보드에서 앱 선택
2. "Settings" → "Secrets" 클릭
3. 위의 TOML 형식으로 입력
4. "Save" 클릭
5. 앱이 자동으로 재배포됨

### 4. EC2 IP 변경 시

EC2 IP가 변경되면:
1. Streamlit Cloud 대시보드 → Settings → Secrets
2. `SERVER_URL` 값 업데이트
3. 자동으로 재배포됨

## 🔄 대안 플랫폼

Streamlit Cloud 외에도 다음 플랫폼들을 사용할 수 있습니다:

### Railway
- https://railway.app
- GitHub 연동 지원
- 환경 변수 설정 가능
- 무료 티어 제공

### Render
- https://render.com
- GitHub 연동 지원
- 환경 변수 설정 가능
- 무료 티어 제공

### Fly.io
- https://fly.io
- Docker 기반 배포
- 환경 변수 설정 가능

## 📝 참고사항

- `utils.py`는 이미 환경 변수를 사용하도록 수정되어 있습니다.
- Streamlit Cloud에서는 `st.secrets`를 사용합니다.
- 로컬 개발 시에는 `.env` 파일이나 환경 변수를 사용할 수 있습니다.

