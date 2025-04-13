# Kakao QA Automation Framework

![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## Overview

Kakao QA Automation Framework는 카카오 서비스의 품질을 보장하기 위한 자동화된 테스트 프레임워크입니다. 이 프레임워크는 API 테스트, UI 테스트, 그리고 Jira와의 통합을 통해 종합적인 품질 관리 솔루션을 제공합니다.

## 주요 기능

- **자동화된 테스트 실행**: API 및 UI 테스트를 자동으로 실행하고 결과를 분석
- **Jira 통합**: 실패한 테스트 케이스를 자동으로 Jira 이슈로 생성
- **상세한 테스트 리포트**: PDF 형식의 상세한 테스트 리포트 생성
- **모니터링 대시보드**: 실시간 테스트 상태 모니터링
- **테스트 케이스 관리**: 구조화된 테스트 케이스 관리 시스템

## 프로젝트 구조

```
kakaofy-qa/
├── api_server/          # API 서버 구현
├── test_engine/         # 테스트 엔진 코어
├── integrations/        # Jira 등 외부 시스템 통합
├── qa_ui/              # QA 대시보드 UI
├── cases/              # 테스트 케이스 정의
├── results/            # 테스트 결과 저장
├── issues/             # Jira 이슈 데이터
└── reports/            # 테스트 리포트
```

## 시작하기

### 필수 요구사항

- Python 3.8 이상
- Node.js 14 이상
- Jira 계정 (선택적)

### 설치

1. 저장소 클론:
```bash
git clone https://github.com/MaduJoe/kakaofy-qa.git
cd kakaofy-qa
```

2. Python 의존성 설치:
```bash
pip install -r requirements.txt
```

3. Node.js 의존성 설치:
```bash
npm install
```

4. 환경 변수 설정:
```bash
cp .env.example .env
# .env 파일을 편집하여 필요한 설정을 입력
```

### 실행 방법

1. API 서버 시작:
```bash
python api_server/app.py
```

2. 테스트 실행:
```bash
python run_test.py
```

3. QA 대시보드 접속:
```
http://localhost:5000
```

## 주요 컴포넌트

### Test Engine
- 테스트 케이스 실행 및 결과 분석
- 실패한 테스트의 자동 Jira 이슈 생성
- 상세한 테스트 리포트 생성

### QA Dashboard
- 실시간 테스트 상태 모니터링
- 테스트 결과 시각화
- 테스트 케이스 관리 인터페이스

### Jira Integration
- 실패한 테스트의 자동 이슈 생성
- 이슈 상태 추적 및 업데이트
- 테스트 결과와 이슈의 연동

## 기여 방법

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 라이센스

이 프로젝트는 MIT 라이센스 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 연락처

Jaekeun Cho - [GitHub](https://github.com/MaduJoe)

프로젝트 링크: [https://github.com/MaduJoe/kakaofy-qa](https://github.com/MaduJoe/kakaofy-qa) 