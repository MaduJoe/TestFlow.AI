
# 🧪 QA Automation Framework

**QA Automation Framework**는 테스트 케이스의 생성부터 실행, 결과 분석, 보고서 생성까지 QA 업무 전반을 자동화하는 플랫폼입니다.  
AI 기반 테스트 케이스 생성 기능과 Postman 기반의 자동화 테스트 실행을 통합하여, 빠르고 신뢰성 높은 품질 보증 프로세스를 제공합니다.

---

## 📌 주요 기능

- 🤖 **AI 기반 테스트 케이스 자동 생성**
- 🌐 **다양한 환경 (개발/스테이징/운영)에서 테스트 실행**
- 📊 **테스트 결과 대시보드 및 상세 분석**
- ✍️ **테스트 케이스 검색, 편집, 재실행**
- 🧾 **테스트 리포트 생성 및 PDF 출력**
- 🔗 **JIRA / Slack 연동으로 협업 강화**

---

## 🖼️ 데모 스크린샷

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

![설정](demo-images/7.%20설정.png)  
👉 JIRA, Slack 등 외부 시스템 연동 관리

---

## ⚙️ 시작하기

### ✅ 사전 요구사항

- Python 3.8 이상
- Node.js (Postman Collection 실행용)

### 📦 설치

```bash
# 저장소 클론
git clone https://github.com/MaduJoe/kakaofy-qa.git
cd kakaofy-qa

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

## 📄 라이센스

MIT License 하에 배포됩니다.  
자세한 내용은 [LICENSE](LICENSE) 파일을 확인해주세요.

---

## 📬 연락처

**Jaekeun Cho**  
🔗 [GitHub](https://github.com/MaduJoe)  
📧 jaekeunv@gmail.com  
📁 프로젝트 링크: [github.com/MaduJoe/kakaofy-qa](https://github.com/MaduJoe/kakaofy-qa)

---
