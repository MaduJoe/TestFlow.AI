import os
import json
import google.generativeai as genai
from datetime import datetime
from dotenv import load_dotenv
import re

# 환경 변수 로드
load_dotenv()

class TestCaseGenerator:
    def __init__(self):
        self.api_key = os.getenv('GOOGLE_API_KEY')
        self.cases_dir = os.getenv('TEST_CASES_DIR', 'cases')
        
        # Gemini API 설정
        genai.configure(api_key=self.api_key)
        
        # 사용 가능한 모델 확인
        available_models = genai.list_models()
        model_names = [model.name for model in available_models]
        # print("Available models:", model_names)
        
        # gemini-pro 모델 사용
        self.model = genai.GenerativeModel('gemini-2.0-flash-lite-preview-02-05')
        
        # cases 디렉토리가 없으면 생성
        if not os.path.exists(self.cases_dir):
            os.makedirs(self.cases_dir)

    def extract_json_from_response(self, text):
        """
        응답 텍스트에서 JSON 부분을 추출합니다.
        """
        # JSON 형식의 텍스트를 찾기 위한 정규식
        json_pattern = r'\{[\s\S]*\}'
        match = re.search(json_pattern, text)
        
        if match:
            try:
                # 추출된 JSON 문자열을 파싱
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                # JSON 파싱 실패 시 기본 테스트 케이스 반환
                return self.create_default_test_case()
        else:
            # JSON 형식이 없는 경우 기본 테스트 케이스 반환
            return self.create_default_test_case()

    def create_default_test_case(self):
        """
        기본 테스트 케이스 템플릿을 생성합니다.
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return {
            "id": f"TC_{timestamp}",
            "method": "GET",  # 기본 HTTP 메서드
            "test_case_id": f"TC_{timestamp}",
            "title": "테스트 케이스",
            "description": "AI가 생성한 테스트 케이스",
            "steps": [
                {
                    "step_id": 1,
                    "action": "테스트 단계",
                    "expected_result": "기대 결과"
                }
            ],
            "preconditions": ["전제 조건"],
            "postconditions": ["후행 조건"],
            "tags": ["테스트"],
            "test_type": "ai_collection"  # 기본 테스트 타입을 ai_collection으로 설정
        }

    def generate_test_case(self, natural_language_request):
        """
        자연어 요청을 받아 Gemini를 통해 테스트 케이스를 생성합니다.
        """
        try:
            # Gemini 프롬프트 구성
            prompt = f"""
            다음 요청에 대한 테스트 케이스를 JSON 형식으로 생성해주세요.
            반드시 아래 형식의 JSON만 응답해주세요. 다른 텍스트는 포함하지 마세요.

            요청: {natural_language_request}

            응답 형식:
            {{
                "id": "TC_타임스탬프",
                "method": "HTTP 메서드 (GET, POST, PUT, DELETE 중 하나)",
                "test_case_id": "TC_타임스탬프",
                "title": "테스트 케이스 제목",
                "description": "테스트 케이스 설명",
                "steps": [
                    {{
                        "step_id": 1,
                        "action": "수행할 동작",
                        "expected_result": "기대 결과"
                    }}
                ],
                "preconditions": ["전제 조건"],
                "postconditions": ["후행 조건"],
                "tags": ["태그1", "태그2"],
                "test_type": "ai_collection"
            }}

            주의사항:
            1. id와 test_case_id는 동일한 값이어야 합니다.
            2. method는 반드시 GET, POST, PUT, DELETE 중 하나여야 합니다.
            3. steps 배열에는 최소 하나 이상의 단계가 포함되어야 합니다.
            4. test_type은 반드시 "ai_collection"으로 설정해야 합니다.
            """

            # Gemini API 호출
            response = self.model.generate_content(prompt)
            
            # 응답에서 JSON 추출
            test_case = self.extract_json_from_response(response.text)
            
            # 필수 필드가 없는 경우 기본값 설정
            if "id" not in test_case:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                test_case["id"] = f"TC_{timestamp}"
                test_case["test_case_id"] = f"TC_{timestamp}"
            if "method" not in test_case:
                test_case["method"] = "GET"
            
            # save_test_case 메서드를 사용하여 파일 저장
            test_case_id = self.save_test_case(test_case)
            
            return {
                "status": "success",
                "test_case_id": test_case_id,
                "test_case": test_case
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    def get_all_test_cases(self):
        """
        저장된 모든 테스트 케이스를 반환합니다.
        """
        test_cases = []
        for filename in os.listdir(self.cases_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(self.cases_dir, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    test_case = json.load(f)
                    test_case['filepath'] = filepath
                    test_cases.append(test_case)
        return test_cases

    def save_test_case(self, test_case: dict) -> str:
        """테스트 케이스를 파일로 저장합니다."""
        # 테스트 케이스 ID 생성
        test_case_id = f"test_case_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        test_case["id"] = test_case_id
        
        # test_type이 설정되지 않았으면 기본값으로 설정
        if "test_type" not in test_case:
            test_case["test_type"] = "ai_collection"
        
        # title을 분석하여 적절한 기능 폴더 결정
        title = test_case.get("title", "").lower()
        feature_folder = "기타"  # 기본 폴더
        
        # title에 포함된 키워드로 기능 폴더 결정
        if any(keyword in title for keyword in ["결제", "payment", "pay", "카드", "계좌"]):
            feature_folder = "결제"
        elif any(keyword in title for keyword in ["로그인", "login", "signin", "로그인", "인증"]):
            feature_folder = "로그인"
        elif any(keyword in title for keyword in ["주문", "order", "구매", "장바구니", "cart"]):
            feature_folder = "주문"
        elif any(keyword in title for keyword in ["회원가입", "signup", "register", "가입", "회원"]):
            feature_folder = "회원가입"
        
        # 기능 폴더 경로 생성
        feature_dir = os.path.join("cases", feature_folder)
        os.makedirs(feature_dir, exist_ok=True)
        
        # 파일 경로 생성
        filepath = os.path.join(feature_dir, f"{test_case_id}.json")
        
        # 파일 저장
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(test_case, f, ensure_ascii=False, indent=2)
        
        return test_case_id 