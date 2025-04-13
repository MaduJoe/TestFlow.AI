from test_engine.test_runner import run_test_case
import json
import os
import sys

def run_test():
    print("실패 테스트 케이스 실행 중...")
    
    try:
        # 현재 디렉토리 확인
        print(f"현재 디렉토리: {os.getcwd()}")
        print(f"파이썬 경로: {sys.path}")
        
        # 존재하지 않는 엔드포인트 호출 테스트
        with open('cases/로그인/test_case_20250413_030015.json', 'r', encoding='utf-8') as f:
            case = json.load(f)
            result = run_test_case(case)
            print(f"테스트 1 결과: {result['result']} - {result.get('status_code', 'N/A')}")
        
        # 잘못된 인증 정보로 결제 시도 테스트
        with open('cases/결제/test_case_20250413_030142.json', 'r', encoding='utf-8') as f:
            case = json.load(f)
            result = run_test_case(case)
            print(f"테스트 2 결과: {result['result']} - {result.get('status_code', 'N/A')}")
        
        # 잘못된 형식의 주문 데이터로 요청 테스트
        with open('cases/주문/test_case_20250413_030255.json', 'r', encoding='utf-8') as f:
            case = json.load(f)
            result = run_test_case(case)
            print(f"테스트 3 결과: {result['result']} - {result.get('status_code', 'N/A')}")
    
    except Exception as e:
        print(f"오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_test() 