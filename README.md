# QA Automation Framework

카카오 QA 자동화 프레임워크는 테스트 케이스 생성부터 실행, 결과 분석까지 전체 QA 프로세스를 자동화하는 강력한 도구입니다. AI를 활용한 테스트 케이스 생성과 Postman Collection 실행 기능을 통합하여 효율적인 QA 프로세스를 지원합니다.

## 주요 기능

- AI를 활용한 테스트 케이스 자동 생성
- 다양한 환경에서의 테스트 실행 지원 (개발, 스테이징, 운영)
- 테스트 결과 대시보드 및 분석 도구
- 테스트 케이스 관리 및 편집
- 보고서 생성 및 PDF 출력
- JIRA 및 Slack 통합

## 스크린샷

### 1. 테스트 케이스 생성

AI를 활용하여 자연어로 테스트 케이스를 생성할 수 있습니다.

![테스트 케이스 생성 1](demo-images/1.1%20테스트케이스생성1.png)
👉*자연어로 테스트 케이스 요청 작성*

![테스트 케이스 생성 2](demo-images/1.2%20테스트케이스생성2.png)
👉*생성된 테스트 케이스 결과*

### 2. 테스트 실행

생성된 테스트 케이스를 선택하여 다양한 환경에서 실행할 수 있습니다.

![테스트 실행](demo-images/2.%20테스트실행.png)
👉*테스트 실행 화면*

### 3. 결과 확인

테스트 실행 결과를 확인하고 보고서를 생성할 수 있습니다.

![결과 확인 1](demo-images/3.1%20결과확인1.png)
👉*테스트 결과 대시보드*

![결과 확인 2](demo-images/3.2%20결과확인2.png)
👉*테스트 보고서 생성*

### 4. 테스트 케이스 관리

생성된 테스트 케이스를 검색, 편집, 관리할 수 있습니다.

![테스트 케이스 관리](demo-images/4.%20테스트케이스관리.png)
👉*테스트 케이스 관리 화면*

### 5. 대시보드

테스트 실행 추이, 커버리지, 실패 패턴 등을 시각화하여 보여줍니다.

![대시보드](demo-images/5.%20대시보드.png)
👉*테스트 대시보드*

### 6. 결과 분석

테스트 결과를 더 깊이 분석하고 비교할 수 있습니다.

![결과 분석](demo-images/6.%20결과분석.png)
👉*테스트 결과 분석 및 비교*

### 7. 설정

JIRA, Slack 연동 등 다양한 설정을 관리할 수 있습니다.

![설정](demo-images/7.%20설정.png)
👉*시스템 설정 화면*

## 시작하기

### 필수 요구사항

- Python 3.8 이상
- Node.js (Postman Collection 실행용)

### 설치 방법

```bash
# 저장소 클론
git clone https://github.com/MaduJoe/kakaofy-qa.git
cd kakaofy-qa

# Python 의존성 설치
pip install -r requirements.txt

# Node.js 의존성 설치
npm install
```

### 실행 방법

```bash
# Streamlit UI 실행
streamlit run qa_ui/app.py
```

## 사용된 기술

- **Backend**: Python, FastAPI
- **Frontend**: Streamlit
- **AI**: Google Gemini AI
- **테스트 도구**: Requests, Newman (Postman CLI)
- **시각화**: Plotly, Altair
- **통합**: JIRA API, Slack Webhooks

## 기여하기

프로젝트에 기여하고 싶으시다면 이슈를 등록하거나 PR을 보내주세요. 모든 기여를 환영합니다!

## 라이센스

이 프로젝트는 MIT 라이센스 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 연락처

Jaekeun Cho - [GitHub](https://github.com/MaduJoe) / Mail : jaekeunv@gmail.com

프로젝트 링크: [https://github.com/MaduJoe/kakaofy-qa](https://github.com/MaduJoe/kakaofy-qa) 
