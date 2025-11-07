# CS4CT (Customer Service for Channel Talk)

> 🤖 LangGraph 기반 AI 부서 배정 시스템

고객 문의를 자동으로 분석하여 적절한 부서에 배정하는 AI 에이전트입니다. LangGraph를 활용하여 일반 채팅과 부서 배정을 동적으로 선택하고, KURE 임베딩 모델로 의미론적 유사도를 계산합니다.

---

## 👥 Team

| 이름 | 역할 | GitHub |
|------|------|--------|
| 김은희 | Design | [@hephee](https://github.com/hephee) |
| 문범용 | Frontend | [@Blay210](https://github.com/Blay210) |
| 임동하 | AI | [@donghalim7](https://github.com/donghalim7) |
| 홍재백 | Backend | [@Kaiden-13D](https://github.com/Kaiden-13D) |

---

## 📁 Project Structure

```
cs4ct/
├── backend/              # Flask API 서버
│   ├── agent.py         # LangGraph 기반 부서 배정 에이전트
│   ├── app.py           # Flask REST API
│   ├── main.py          # 테스트 스크립트
│   ├── Dockerfile       # Docker 컨테이너 설정
│   ├── pyproject.toml   # 패키지 의존성 (uv)
│   └── requirements.txt # 패키지 의존성 (pip)
│
├── frontend/            # Streamlit UI
│   ├── app.py          # 메인 UI 애플리케이션
│   ├── supabase_config.py # Supabase 설정
│   ├── utils.py        # 유틸리티 함수
│   ├── requirements.txt # 프론트엔드 의존성
│   └── README_DEPLOY.md # Streamlit Cloud 배포 가이드
│
└── README.md           # 프로젝트 문서 (이 파일)
```

---

## 🚀 Features

### 🎯 핵심 기능
- **LangGraph 기반 워크플로우**: LLM이 자동으로 일반 채팅과 부서 배정을 선택
- **의미론적 검색**: KURE-v1 임베딩 모델로 한국어 의미 이해
- **동적 부서 선택**: GPT-4o-mini가 top-k 후보 중 최적 부서 선택
- **REST API**: Flask 기반 API 서버로 쉬운 통합
- **실시간 UI**: Streamlit 기반 대화형 인터페이스

### 🔍 기술 스택

#### Backend
- **Framework**: Flask 3.0.0 + Flask-CORS
- **AI/ML**:
  - LangGraph: 멀티 에이전트 워크플로우
  - LangChain: LLM 통합 프레임워크
  - OpenAI GPT-4o-mini: 부서 선택 및 채팅
  - KURE-v1: 한국어 임베딩 (nlpai-lab/KURE-v1)
- **Database**: Supabase (PostgreSQL)
- **Others**: Python 3.12+, Docker

#### Frontend
- **Framework**: Streamlit
- **Database**: Supabase
- **Deployment**: Streamlit Cloud

---

## 🛠️ Installation

### Prerequisites
- Python 3.12 이상
- Supabase 계정 및 프로젝트
- OpenAI API 키

### 1. Clone Repository

```bash
git clone <repository-url>
cd cs4ct
```

### 2. Backend Setup

#### Option A: Using `uv` (권장)

```bash
cd backend
uv sync
```

#### Option B: Using `pip`

```bash
cd backend
pip install -r requirements.txt
```

### 3. Environment Variables

`backend/.env` 파일 생성:

```bash
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
OPENAI_API_KEY=your_openai_api_key
```

### 4. Database Schema

Supabase에 다음 테이블을 생성하세요:

#### `message` 테이블
```sql
CREATE TABLE message (
  msg_id TEXT PRIMARY KEY,
  content TEXT NOT NULL
);
```

#### `department_imsi` 테이블
```sql
CREATE TABLE department_imsi (
  dept_id TEXT PRIMARY KEY,
  dept_name TEXT NOT NULL,
  dept_desc TEXT NOT NULL
);
```

#### `assigned_message` 테이블
```sql
CREATE TABLE assigned_message (
  dept_id TEXT NOT NULL,
  msg_id TEXT NOT NULL,
  PRIMARY KEY (dept_id, msg_id),
  FOREIGN KEY (dept_id) REFERENCES department_imsi(dept_id),
  FOREIGN KEY (msg_id) REFERENCES message(msg_id)
);
```

---

## 💻 Usage

### Backend API 서버 실행

```bash
cd backend
python app.py
```

서버는 `http://localhost:8000`에서 실행됩니다.

### API Endpoints

#### POST `/assign-department`

고객 문의를 분석하여 부서에 배정합니다.

**Request:**
```json
{
  "msg_id": "12345",
  "top_k": 5
}
```

**Response:**
```json
{
  "status": 1,
  "message": "부서 배정 완료"
}
```

- `status`: `0` (일반 채팅) 또는 `1` (부서 배정 완료)

### Frontend UI 실행

```bash
cd frontend
streamlit run app.py
```

UI는 `http://localhost:8501`에서 실행됩니다.

---

## 🧪 Testing

### 에이전트 테스트

```bash
cd backend
python main.py
```

로그를 통해 다음을 확인할 수 있습니다:
- 검색된 유사 부서 (ID, 이름, 유사도)
- LLM의 부서 선택 결과
- DB 저장 여부

---

## 🐳 Docker Deployment

### Build Image

```bash
cd backend
docker build -t cs4ct-backend .
```

### Run Container

```bash
docker run -d \
  -p 8000:8000 \
  -e SUPABASE_URL=your_supabase_url \
  -e SUPABASE_KEY=your_supabase_key \
  -e OPENAI_API_KEY=your_openai_api_key \
  --name cs4ct-backend \
  cs4ct-backend
```

---

## 🌐 Frontend Deployment

Streamlit Cloud에 프론트엔드를 배포하려면 [`frontend/README_DEPLOY.md`](frontend/README_DEPLOY.md)를 참고하세요.

---

## 🔧 Architecture

```
┌─────────────┐
│   고객 문의   │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────┐
│  LangGraph Agent (agent.py)     │
│  ┌───────────────────────────┐  │
│  │ 1. Intent Classification  │  │  ← GPT-4o-mini decides
│  │    (Chat vs Assignment)   │  │
│  └─────────────┬─────────────┘  │
│                │                 │
│    ┌───────────┴────────────┐   │
│    ▼                        ▼   │
│  ┌──────┐            ┌──────────┐
│  │ Chat │            │ Assignment│
│  └──────┘            └─────┬────┘
│                            │     │
│                ┌───────────┴───────────┐
│                ▼                       │
│       ┌──────────────────┐             │
│       │ KURE Embedding   │             │
│       │ (Top-K Search)   │             │
│       └────────┬─────────┘             │
│                ▼                       │
│       ┌──────────────────┐             │
│       │ GPT-4o-mini      │             │
│       │ (Dept Selection) │             │
│       └────────┬─────────┘             │
│                ▼                       │
│       ┌──────────────────┐             │
│       │ Save to Supabase │             │
│       └──────────────────┘             │
└─────────────────────────────────────────┘
       │
       ▼
┌─────────────┐
│   Response  │
└─────────────┘
```

---

## 📝 How It Works

### 1. **메시지 입력**
사용자가 문의를 입력하면 `message` 테이블에 저장됩니다.

### 2. **LangGraph 워크플로우**
- **Chatbot Node**: LLM이 메시지를 분석하고 도구 사용 여부 결정
  - 일반 채팅: 바로 응답 생성
  - 부서 배정: `assign_department_tool` 호출

### 3. **부서 검색 (assign_department_tool)**
- KURE-v1로 메시지와 모든 부서 설명을 임베딩
- 코사인 유사도로 top-k 후보 부서 선택

### 4. **최종 부서 선택**
- GPT-4o-mini가 top-k 후보를 분석하여 최적 부서 선택
- 여러 부서가 관련될 수 있으면 다중 선택 가능

### 5. **결과 저장**
- 선택된 부서를 `assigned_message` 테이블에 저장
- 프론트엔드/API 응답 반환

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

이 프로젝트는 MIT 라이선스를 따릅니다.

---

## 🙏 Acknowledgments

- **KURE Embedding Model**: [nlpai-lab/KURE-v1](https://github.com/nlpai-lab/KURE)
- **LangGraph**: [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- **OpenAI**: GPT-4o-mini API
- **Supabase**: Database and Backend Services

---

## 📧 Contact

프로젝트에 대한 질문이나 제안이 있으시면 이슈를 등록해주세요!
