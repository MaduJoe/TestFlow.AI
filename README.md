# 🧪 TestFlow with AI

이 프로젝트는 **테스트 케이스 생성부터 실행, 결과 분석까지 QA 업무 전반을 AI 기술로 자동화**하는 **통합 QA 플랫폼**입니다.

- **Google Gemini API**를 활용한 **자연어 기반 테스트케이스 자동 생성** 기능을 제공합니다.
- **Postman 기반 API 테스트 자동화**를 통해 다양한 테스트 시나리오를 신속하게 검증합니다.
- **개발/스테이징/운영 환경**을 구분하여 테스트를 **멀티 환경에서 실행**할 수 있도록 지원합니다.
- **Streamlit + FastAPI** 기반의 **직관적인 웹 UI**로 테스트 과정을 쉽게 시각화할 수 있습니다.
- **Plotly 및 Altair**를 활용한 **데이터 시각화** 기능을 통해 테스트 결과에 대한 **인사이트를 도출**합니다.
- **JIRA 및 Slack 연동**을 통해 테스트 결과 공유 및 협업 효율성을 향상시켰습니다.
- **Python과 Node.js 기반의 확장 가능한 아키텍처**로 구성되어, 다양한 QA 워크플로우에 유연하게 대응할 수 있습니다.

> 🤖 AI 기술을 중심으로 QA 업무를 혁신하며, **자동화, 협업, 시각화가 통합된 스마트한 테스트 플랫폼**을 지향합니다.

---

## 주요 기능

- 🤖 **AI 기반 테스트 케이스 자동 생성**
- 🌐 **다양한 환경 (개발/스테이징/운영)에서 테스트 실행**
- 📊 **테스트 결과 대시보드 및 상세 분석**
- ✍️ **테스트 케이스 검색, 편집, 재실행**
- 🧾 **테스트 리포트 생성 및 PDF 출력**
- 🔗 **JIRA / Slack 연동으로 협업 강화**

---

## 스크린샷

### 🧠 1. 테스트 케이스 생성 (AI 기반)

| 자연어 요청 | 생성 결과 |
|-------------|------------|
| ![생성 요청](demo-images/1.1%20테스트케이스생성1.png) | ![생성 결과](demo-images/1.2%20테스트케이스생성2.png) |

---

### 🚀 2. 테스트 실행

![테스트 실행](demo-images/2.%20테스트실행.png)  
👉 다양한 환경을 선택하여 자동 실행

---

### 📋 3. 결과 확인 및 리포트

| 대시보드 | 보고서 |
|----------|---------|
| ![대시보드](demo-images/3.1%20결과확인1.png) | ![보고서](demo-images/3.2%20결과확인2.png) |

---

### 🗂️ 4. 테스트 케이스 관리

![테스트 케이스 관리](demo-images/4.%20테스트케이스관리.png)  
👉 테스트 케이스의 검색, 복사, 삭제, 재실행 지원

---

### 📈 5. 테스트 대시보드

![대시보드](demo-images/5.%20대시보드.png)  
👉 실행 통계, 커버리지, 실패 추이 등 시각화 제공

---

### 🔍 6. 결과 분석

![분석](demo-images/6.%20결과분석.png)  
👉 테스트 결과 비교 및 상세 원인 분석

---

### ⚙️ 7. 설정 관리

| 연동 설정 | 연동 결과 |
|-----------|-----------|
| ![설정1](demo-images/7.1%20설정.png) | ![설정2](demo-images/7.2%20설정.png) |

---

## 시작하기

### ✅ 사전 요구사항

- Python 3.8 이상
- Node.js (Postman Collection 실행용)

### 📦 설치

```bash
# 저장소 클론
git clone https://github.com/MaduJoe/TestFlow.AI.git
cd TestFlow.AI

# Python 의존성 설치
pip install -r requirements.txt

# Node.js 의존성 설치
npm install
```

### ▶️ 실행

```bash
# Streamlit UI 실행
streamlit run qa_ui/app.py

# API 서버 실행
python api_server/app.py

# 백엔드 로직 서버 실행
python app/main.py 
```

---

## 🛠 기술 스택

| 영역 | 기술 |
|------|------|
| Backend | Python, FastAPI |
| Frontend | Streamlit |
| AI | Google Gemini API |
| Test Automation | Requests, Newman (Postman CLI) |
| Data Visualization | Plotly, Altair |
| Integration | JIRA API, Slack Webhooks |

---

## 🙌 기여하기

Pull Request와 Issue 환영합니다!  
기여 전에는 간단한 설명이나 사전 논의해 주시면 더욱 좋아요.

---

## 📬 연락처

**Jaekeun Cho**  
🔗 [GitHub](https://github.com/MaduJoe)  
📧 jaekeunv@gmail.com  
📁 프로젝트 링크: [github.com/MaduJoe/TestFlow.AI](https://github.com/MaduJoe/TestFlow.AI)

---
