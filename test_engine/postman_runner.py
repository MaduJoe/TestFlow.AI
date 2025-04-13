import subprocess
import os
import sys
import json
from datetime import datetime

def run_postman_collection(collection_path=None):
    # 현재 파일의 디렉토리 경로를 기준으로 절대 경로 설정
    current_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(current_dir)
    
    # collection_path가 제공되지 않은 경우 기본 경로 사용
    if collection_path is None:
        collection_path = os.path.join(root_dir, "postman", "kakao_qa_collection.json")
    else:
        # 상대 경로인 경우 절대 경로로 변환
        if not os.path.isabs(collection_path):
            collection_path = os.path.join(root_dir, collection_path)
    
    output_path = os.path.join(root_dir, "logs", "postman_result.json")

    if not os.path.exists(collection_path):
        return {"status": "fail", "error": f"❗ Postman collection 파일을 찾을 수 없습니다: {collection_path}"}

    try:
        # Windows에서는 npx를 사용하여 newman 실행
        command = f'npx newman run "{collection_path}" --reporters cli,json --reporter-json-export "{output_path}"'
        
        # shell=True를 사용하여 명령어 실행
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            check=True
        )
        
        # JSON 결과 파일 읽기
        with open(output_path, 'r', encoding='utf-8') as f:
            json_result = json.load(f)
        
        # 결과를 더 읽기 쉽게 포맷팅
        formatted_result = format_postman_result(json_result)
        
        return {
            "status": "success",
            "output": formatted_result,
            "report_path": output_path,
            "raw_result": json_result
        }
    except subprocess.CalledProcessError as e:
        return {
            "status": "fail",
            "error": e.stderr
        }
    except Exception as e:
        return {
            "status": "fail",
            "error": str(e)
        }

def format_postman_result(result):
    """
    Postman 테스트 결과를 읽기 쉽게 포맷팅합니다.
    """
    formatted = []
    
    # 실행 정보
    run_info = result.get('run', {})
    stats = run_info.get('stats', {})
    
    formatted.append("📊 테스트 실행 결과")
    formatted.append(f"실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    formatted.append(f"총 요청 수: {stats.get('requests', {}).get('total', 0)}")
    formatted.append(f"성공: {stats.get('requests', {}).get('passed', 0)}")
    formatted.append(f"실패: {stats.get('requests', {}).get('failed', 0)}")
    formatted.append("\n📝 상세 결과:")
    
    # 각 요청의 결과
    executions = run_info.get('executions', [])
    for idx, execution in enumerate(executions, 1):
        request = execution.get('request', {})
        response = execution.get('response', {})
        
        # 요청 이름 가져오기 (item.name 또는 request.name에서 찾기)
        request_name = request.get('name', '')
        if not request_name:
            # item에서 이름 찾기
            item = execution.get('item', {})
            request_name = item.get('name', '이름 없음')
        
        method = request.get('method', '')
        url = request.get('url', {}).get('raw', '')
        
        # URL에서 마지막 경로를 이름으로 사용 (이름이 없는 경우)
        if request_name == '이름 없음' and url:
            path_parts = url.split('/')
            if len(path_parts) > 1:
                request_name = path_parts[-1]
        
        formatted.append(f"\n{idx}. {method} - {request_name}")
        formatted.append(f"   URL: {url}")
        formatted.append(f"   상태 코드: {response.get('code', '')}")
        formatted.append(f"   상태: {'✅ 성공' if execution.get('response', {}).get('code', 0) < 400 else '❌ 실패'}")
        
        # 실패한 경우 상세 정보 추가
        if execution.get('response', {}).get('code', 0) >= 400:
            formatted.append(f"   실패 사유: {response.get('status', '')}")
            formatted.append(f"   응답 본문: {response.get('body', '')}")
    
    return "\n".join(formatted)
