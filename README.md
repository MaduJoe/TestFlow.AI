# 📊 TestFlow AI: 스트림릿 기반 QA 자동화 통합 플랫폼

이 프로젝트는 **스트림릿 기반의 QA 테스트 자동화 플랫폼**으로, **테스트 케이스 관리 기능과 테스트 실행 자동화**를 통합하여 테스트 프로세스를 간소화합니다.

* **직관적인 웹 인터페이스**를 통해 테스트 케이스를 **생성, 관리, 실행**할 수 있으며, **실시간 결과 시각화 대시보드**를 제공합니다.
* **AI 통합 기능**을 통해:  
   * **자연어로 테스트 케이스 자동 생성**  
   * **지능형 테스트 결과 분석**  
   * **실패 패턴 자동 감지**가 가능합니다.
* **백그라운드 워커와 스케줄러**를 활용해 **예약된 테스트 실행**을 지원합니다.
* **Plotly와 Altair**를 사용하여 **인터랙티브 차트**로 테스트 결과를 시각화합니다.
* **지라 통합**으로 **자동 이슈 생성 및 관리**가 가능합니다.

> 🚀 테스트의 설계부터 실행, 리포트까지 하나의 플랫폼에서 자동화하여 **QA 업무의 생산성과 가시성을 극대화**합니다.

---

## 🖼️ 주요 기능

### 1\. AI 테스트 케이스 생성
* 자연어 입력으로 테스트 케이스 자동 생성
* Google Gemini API 활용
* 테스트 유형에 따른 자동 분류 및 저장

### 2\. 테스트 실행 및 모니터링
* AI 생성 테스트 케이스 및 Postman 컬렉션 실행 지원
* 테스트 환경 선택 기능 (개발, 스테이징, 운영)
* 예약 실행 기능 (일회성, 매일, 매주, 매월)

### 3\. 결과 시각화 및 분석
* 성공/실패 비율 인터랙티브 차트
* 테스트 실행 추이 시각화
* 테스트 케이스별 통계 및 실패 패턴 분석

### 4\. 보고서 생성
* 상세 테스트 보고서 자동 생성
* PDF 형식 보고서 다운로드 지원
* 테스트 실행 간 비교 보고서 지원

### 5\. 지라 통합
* 실패한 테스트에 대한 자동 지라 이슈 생성
* 이슈 추적 및 관리 기능

---

## 💻 기술 스택

| 영역         | 기술                                 |
| ---------- | ---------------------------------- |
| **백엔드**    | Python, Flask, Streamlit           |
| **프론트엔드**  | Streamlit                          |
| **시각화**    | Plotly, Altair                     |
| **비동기 처리** | APScheduler                        |
| **인공지능**   | Google Gemini API                  |
| **테스트 도구** | Postman/Newman                     |
| **통합**     | Jira API                           |

---

## 🏗️ 시스템 아키텍처

```
[웹 브라우저] <---- HTTP ----> [Streamlit 앱 (qa_ui/app.py)]
                                |         |
[테스트 케이스 저장소] <-------> |         | <--------> [테스트 결과 저장소]
   (cases/*.json)               |         |             (results/*.json)
                                |         |
[API 서버] <-------------------> |         | <--------> [이슈 저장소]
(api_server/app.py)             |         |           (issues/*.json)
                                |         |
                                ↓         ↓
                        [APScheduler (백그라운드 스케줄러)]
                                |
                                ↓
                        [테스트 실행기 (test_engine/test_runner.py)]
                                |
                                ↓
                        [Jira API 연동 (integrations/jira_api.py)]
```

---

## 🔍 주요 컴포넌트

### 1\. Streamlit 앱 (qa_ui/app.py)
* 사용자 인터페이스 제공
* 테스트 케이스 관리 및 실행 기능
* 결과 시각화 및 대시보드

### 2\. 테스트 엔진 (test_engine/)
* 테스트 케이스 로더 및 실행기
* AI 테스트 케이스 생성기
* Postman 컬렉션 실행기

### 3\. API 서버 (api_server/app.py)
* 테스트 대상 API 제공
* 요청 처리 및 응답 생성

### 4\. 통합 컴포넌트 (integrations/)
* Jira API 연동
* 외부 시스템 통합

---

## 📋 고급 기능

### AI 테스트 케이스 생성
* 자연어 입력을 통한 테스트 케이스 자동 생성
* 테스트 유형 자동 분류 (로그인, 회원가입, 주문, 결제 등)
* 구조화된 JSON 형식으로 테스트 케이스 저장

### 스케줄링 시스템
* 유연한 테스트 실행 예약 기능
* 다양한 반복 패턴 지원 (매일, 매주, 매월)
* 백그라운드 작업으로 실행 상태 모니터링

### 데이터 시각화
* 인터랙티브 차트로 테스트 결과 시각화
* 테스트 실행 추이 분석
* 성공/실패 비율 및 커버리지 시각화

---

## 🚀 설치 및 실행 방법

### 필수 요구사항
* Python 3.8 이상
* pip (Python 패키지 관리자)
* 가상 환경 (선택사항이지만 권장)

### 설치 단계
1. 저장소 클론:  
```
git clone https://github.com/yourusername/TestFlow.AI.git
cd TestFlow.AI
```

2. 가상 환경 설정 (선택사항):  
```
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. 의존성 설치:  
```
pip install -r requirements.txt
```

4. 환경 변수 설정:  
```
# .env 파일 편집
GOOGLE_API_KEY=your-gemini-api-key  # AI 기능 사용 시 필요
JIRA_TOKEN=your-jira-token  # 지라 연동 시 필요
JIRA_PROJECT_KEY=your-project-key
```

5. 애플리케이션 실행:
```
cd qa_ui
streamlit run app.py
```

6. API 서버 실행 (별도 터미널):
```
cd api_server
python app.py
```

7. 브라우저에서 접속:
```
http://localhost:8501
```

---

## 스크린샷

### 1. 테스트 케이스 생성

AI를 활용하여 자연어로 테스트 케이스를 생성할 수 있습니다.

![테스트 케이스 생성 1](./demo-images/1.1%20테스트케이스생성1.png)
*자연어로 테스트 케이스 요청 작성*

![테스트 케이스 생성 2](./demo-images/1.2%20테스트케이스생성2.png)
*생성된 테스트 케이스 결과*

### 2. 테스트 실행

생성된 테스트 케이스를 선택하여 다양한 환경에서 실행할 수 있습니다.

![테스트 실행](./demo-images/2.%20테스트실행.png)
*테스트 실행 화면*

### 3. 결과 확인

테스트 실행 결과를 확인하고 보고서를 생성할 수 있습니다.

![결과 확인 1](./demo-images/3.1%20결과확인1.png)
*테스트 결과 대시보드*

![결과 확인 2](./demo-images/3.2%20결과확인2.png)
*테스트 보고서 생성*

### 4. 테스트 케이스 관리

생성된 테스트 케이스를 검색, 편집, 관리할 수 있습니다.

![테스트 케이스 관리](./demo-images/4.%20테스트케이스관리.png)
*테스트 케이스 관리 화면*

### 5. 대시보드

테스트 실행 추이, 커버리지, 실패 패턴 등을 시각화하여 보여줍니다.

![대시보드](./demo-images/5.%20대시보드.png)
*테스트 대시보드*

---

## 📈 향후 개선 계획
* 테스트 커버리지 분석 기능 강화
* 모바일 앱 테스트 자동화 추가
* CI/CD 파이프라인 통합
* 다중 환경 테스트 지원 확장
* AI 기반 테스트 케이스 최적화

---

## 📬 연락처
**재근 조**  
🔗 GitHub: [MaduJoe](https://github.com/MaduJoe)  
📧 jaekeunv@gmail.com

---

© 2025 재근 조 (jaekeunv@gmail.com)
