import os
import json
from datetime import datetime
import requests
from typing import List, Dict, Any, Optional
from test_engine.test_utils import run_test_case
import plotly.graph_objects as go
import pandas as pd
import altair as alt
import sys
# sys.path.append(".")  # 프로젝트 루트 추가
from integrations.jira_api import JiraAPI

CASE_DIR = "cases"
LOG_DIR = "logs"
ISSUE_DIR = "issues"  # 이슈 저장 폴더

def load_all_cases():
    """모든 테스트 케이스를 로드합니다."""
    cases = []
    cases_dir = "cases"
    
    if os.path.exists(cases_dir):
        # cases 디렉토리 하위의 모든 디렉토리와 파일 탐색
        for root, dirs, files in os.walk(cases_dir):
            for file in files:
                if file.endswith(".json"):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            case = json.load(f)
                            # 파일 경로 정보 추가
                            case['filepath'] = file_path
                            cases.append(case)
                    except Exception as e:
                        print(f"Error loading case file {file_path}: {str(e)}")
    
    return cases

def run_test_case(case: Dict[str, Any], env: str = "dev") -> Dict[str, Any]:
    """단일 테스트 케이스를 실행합니다."""
    try:
        # 환경에 따른 API URL 설정
        base_url = get_base_url(env)
        
        # 요청 정보 추출
        method = case.get("method", "GET")
        endpoint = case.get("endpoint", "")
        headers = case.get("headers", {})
        body = case.get("body", {})
        
        # API 요청 실행
        url = f"{base_url}{endpoint}"
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            json=body
        )
        
        # 결과 생성
        result = {
            "id": case.get("id", "unknown"),
            "desc": case.get("description", "No description"),
            "result": "PASS" if response.status_code == case.get("expected_status", 200) else "FAIL",
            "status_code": response.status_code,
            "body": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text,
            "execution_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "env": env,
            "test_type": case.get("test_type", "ai_collection")  # 테스트 케이스에서 test_type 가져오기
        }
        
        # 결과 저장
        save_result(result)
        
        return result
        
    except Exception as e:
        result = {
            "id": case.get("id", "unknown"),
            "desc": case.get("description", "No description"),
            "result": "ERROR",
            "reason": str(e),
            "execution_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "env": env,
            "test_type": case.get("test_type", "ai_collection")  # 테스트 케이스에서 test_type 가져오기
        }
        
        # 오류 결과 저장
        save_result(result)
        
        return result

def run_selected_cases(selected_cases: List[str], env: str = "dev") -> List[Dict[str, Any]]:
    """선택된 테스트 케이스들을 실행합니다."""
    all_cases = load_all_cases()
    results = []
    
    # 선택된 케이스 ID 추출
    selected_ids = [case.split(" - ")[0] for case in selected_cases]
    
    # 선택된 케이스만 필터링
    cases_to_run = [case for case in all_cases if case["id"] in selected_ids]
    
    # 각 케이스 실행
    for case in cases_to_run:
        result = run_test_case(case, env)
        results.append(result)
    
    return results

def get_base_url(env: str) -> str:
    """환경에 따른 기본 URL을 반환합니다."""
    env_urls = {
        "dev": "http://127.0.0.1:5001",
        "staging": "https://staging-api.example.com",
        "prod": "https://api.example.com"
    }
    return env_urls.get(env, env_urls["dev"])

def save_result(result: Dict[str, Any]) -> None:
    """테스트 결과를 저장합니다."""
    results_dir = "results"
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)
    
    # 현재 시간으로 고유한 ID 생성
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    
    # 테스트 ID를 결과에서 가져옴
    test_id = result.get('id', 'unknown')
    
    # 결과 파일의 형식을 변경 (ID만 포함)
    result_file = f"test_result_{timestamp}.json"
    
    # test_type이 없는 경우 기본값 설정
    if "test_type" not in result:
        # 케이스 파일에서 test_type 확인 시도
        try:
            # 케이스 파일 찾기 (cases 디렉토리 내의 모든 JSON 파일 검색)
            case_file = None
            for root, dirs, files in os.walk("cases"):
                for file in files:
                    if file.endswith(".json") and test_id in file:
                        case_file = os.path.join(root, file)
                        break
                if case_file:
                    break
            
            # 케이스 파일에서 test_type 읽기
            if case_file and os.path.exists(case_file):
                with open(case_file, "r", encoding="utf-8") as f:
                    case_data = json.load(f)
                    result["test_type"] = case_data.get("test_type", "ai_collection")
            else:
                # 케이스 파일을 찾지 못한 경우 기본값 설정
                result["test_type"] = "ai_collection"
        except Exception as e:
            print(f"케이스 파일 읽기 중 오류: {str(e)}")
            result["test_type"] = "ai_collection"
    
    # 결과 파일 저장
    result_path = os.path.join(results_dir, result_file)
    
    # 테스트 케이스 ID와 실행 시간을 포함한 전체 결과 작성
    full_result = {
        "id": timestamp,
        "execution_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "env": result.get("env", "개발"),
        "results": [result],
        "type": result.get("test_type", "ai_collection"),  # test_type을 type으로 변환하여 저장
        "scheduled": False
    }
    
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(full_result, f, ensure_ascii=False, indent=2)
    
    # 테스트 케이스와 실행 ID를 연결하는 파일도 저장
    link_file = f"test_result_{test_id}_{timestamp}.json"
    link_path = os.path.join(results_dir, link_file)
    
    link_data = {
        "test_case_id": test_id,
        "execution_id": timestamp,
        "execution_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "result": result.get("result", "UNKNOWN"),
        "type": result.get("test_type", "ai_collection")  # test_type을 type으로 통일
    }
    
    with open(link_path, "w", encoding="utf-8") as f:
        json.dump(link_data, f, ensure_ascii=False, indent=2)

def load_test_history() -> List[Dict[str, Any]]:
    """테스트 실행 이력을 로드합니다."""
    results = []
    results_dir = "results"
    
    if not os.path.exists(results_dir):
        return results
    
    for filename in os.listdir(results_dir):
        if filename.startswith("test_result_") and filename.endswith(".json"):
            with open(os.path.join(results_dir, filename), "r", encoding="utf-8") as f:
                result = json.load(f)
                results.append(result)
    
    return sorted(results, key=lambda x: x["execution_time"], reverse=True)

def save_results(results):
    os.makedirs(LOG_DIR, exist_ok=True)
    filename = f"log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(os.path.join(LOG_DIR, filename), "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, indent=2, ensure_ascii=False) + "\n\n")

def create_issue_file(result):
    """실패한 테스트 결과에 대해 이슈 파일을 생성합니다."""
    # print(f"Sync to Jira : {result}")
    issue_dir = "issues"
    if not os.path.exists(issue_dir):
        os.makedirs(issue_dir)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"issue_{result['id']}_{timestamp}.json"
    filepath = os.path.join(issue_dir, filename)
    
    # 이슈 데이터 구성
    issue_data = {
        "fields": {
            "project": {
                "key": os.getenv('JIRA_PROJECT_KEY', 'PROJECT_KEY')  # 환경 변수에서 프로젝트 키 가져오기
            },
            "summary": f"테스트 케이스 실패: {result['id']}",
            # "description": f"{result.get('desc', 'No description')}\n\n결과: {result['result']}\n이유: {result.get('reason', 'No reason')}\n타임스탬프: {timestamp}\n생성일: {datetime.now().isoformat()}\n상태: OPEN",
            "description": f"{result.get('desc', 'No description')}\n\n결과: {result['result']}\n이유: {result.get('reason', 'No reason')}\n타임스탬프: {timestamp}\n상태: OPEN",
            "issuetype": {
                "name": "Bug"
            }
        } 
    }
    
    # 타임스탬프와 생성일 정보 추가
    result['timestamp'] = timestamp
    # result['created_at'] = datetime.now().isoformat()
    
    # 이슈 파일 저장
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(issue_data, f, ensure_ascii=False, indent=2)
    
    # Jira 이슈 생성 시도
    try:
        create_jira_issue = os.getenv('CREATE_JIRA_ISSUE', 'false').lower() == 'true'
        if create_jira_issue:
            jira_client = JiraAPI()
            project_key = os.getenv('JIRA_PROJECT_KEY')
            
            if project_key:
                issue_result = jira_client.create_test_issue_from_failed_test(result, project_key)
                
                # 이슈 파일 업데이트
                if issue_result.get('success'):
                    issue_data["fields"].update({
                        "jira_key": issue_result.get('issue_key'),
                        "jira_url": issue_result.get('issue_url'),
                        "jira_synced": True
                    })
                    
                    # 업데이트된 이슈 데이터 저장
                    with open(filepath, "w", encoding="utf-8") as f:
                        json.dump(issue_data, f, ensure_ascii=False, indent=2)
                    
                    print(f"Jira 이슈가 생성되었습니다: {issue_result.get('issue_key')}")
                else:
                    print(f"Jira 이슈 생성 실패: {issue_result.get('message')}")
    except Exception as e:
        print(f"Jira 연동 중 오류 발생: {str(e)}")
    
    return filepath

def run_and_report():
    cases = load_all_cases()
    results = [run_test_case(case) for case in cases]
    save_results(results)

    for result in results:
        print(f"[{result['id']}] {result['desc']} => {result['result']}")
        if result["result"] == "FAIL":
            create_issue_file(result)

def filter_cases(cases: List[Dict[str, Any]], search_query: str = "", tags: List[str] = None) -> List[Dict[str, Any]]:
    """테스트 케이스를 검색어와 태그로 필터링합니다."""
    if not search_query and (not tags or len(tags) == 0):
        return cases
    
    filtered = []
    for case in cases:
        # 검색어 필터링
        matches_search = True
        if search_query:
            search_lower = search_query.lower()
            matches_search = (
                search_lower in case.get("title", "").lower() or
                search_lower in case.get("description", "").lower() or
                search_lower in case.get("id", "").lower()
            )
        
        # 태그 필터링
        matches_tags = True
        if tags and len(tags) > 0:
            case_tags = case.get("tags", [])
            matches_tags = any(tag in case_tags for tag in tags)
        
        if matches_search and matches_tags:
            filtered.append(case)
    
    return filtered

def group_cases_by_feature(cases):
    """테스트 케이스를 기능별로 그룹화합니다."""
    grouped_cases = {}
    
    # cases 디렉토리 하위의 모든 디렉토리 찾기
    cases_dir = "cases"
    if os.path.exists(cases_dir):
        for feature_dir in os.listdir(cases_dir):
            feature_path = os.path.join(cases_dir, feature_dir)
            if os.path.isdir(feature_path):
                grouped_cases[feature_dir] = []
    
    # 각 테스트 케이스를 해당하는 기능 디렉토리에 할당
    for case in cases:
        # 테스트 케이스 파일의 경로에서 기능 디렉토리 추출
        case_path = case.get('filepath', '')
        if case_path:
            # cases/기능디렉토리/파일명.json 형식에서 기능 디렉토리 추출
            path_parts = case_path.split(os.sep)
            if len(path_parts) >= 3 and path_parts[0] == 'cases':
                feature = path_parts[1]
                if feature in grouped_cases:
                    grouped_cases[feature].append(case)
                else:
                    # 새로운 기능 디렉토리가 발견된 경우
                    grouped_cases[feature] = [case]
    
    return grouped_cases

def update_case_priority(case_id: str, priority: str) -> bool:
    """테스트 케이스의 우선순위를 업데이트합니다."""
    try:
        cases = load_all_cases()
        for case in cases:
            if case["id"] == case_id:
                case["priority"] = priority
                save_case(case)
                return True
        return False
    except Exception:
        return False

def save_case(case: Dict[str, Any]) -> None:
    """테스트 케이스를 저장합니다."""
    cases_dir = "cases"
    if not os.path.exists(cases_dir):
        os.makedirs(cases_dir)
    
    filename = f"test_case_{case['id']}.json"
    with open(os.path.join(cases_dir, filename), "w", encoding="utf-8") as f:
        json.dump(case, f, ensure_ascii=False, indent=2)

def delete_case(case_id: str) -> bool:
    """테스트 케이스를 삭제합니다."""
    try:
        filename = f"test_case_{case_id}.json"
        filepath = os.path.join("cases", filename)
        if os.path.exists(filepath):
            os.remove(filepath)
            return True
        return False
    except Exception:
        return False

def plot_test_trend(test_history: List[Dict[str, Any]]) -> go.Figure:
    """테스트 실행 추이를 시각화합니다."""
    if not test_history:
        # 빈 데이터로 기본 그래프 생성
        fig = go.Figure()
        fig.add_annotation(
            text="테스트 실행 이력이 없습니다",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False
        )
        return fig
    
    # 데이터프레임 생성
    data = []
    for history in test_history:
        if history.get('type') == 'test_case':
            for result in history.get('results', []):
                data.append({
                    'execution_time': history['execution_time'],
                    'result': result.get('result', 'UNKNOWN'),
                    'test_id': result.get('id', 'UNKNOWN')
                })
        elif history.get('type') == 'postman':
            postman_result = history.get('postman_result', {})
            if postman_result.get('status') == 'success':
                output_lines = postman_result.get('output', '').split('\n')
                for line in output_lines:
                    if '✅' in line:
                        data.append({
                            'execution_time': history['execution_time'],
                            'result': 'PASS',
                            'test_id': line.split(' - ')[0] if ' - ' in line else 'UNKNOWN'
                        })
                    elif '❌' in line:
                        data.append({
                            'execution_time': history['execution_time'],
                            'result': 'FAIL',
                            'test_id': line.split(' - ')[0] if ' - ' in line else 'UNKNOWN'
                        })
                    elif '⚠️' in line:
                        data.append({
                            'execution_time': history['execution_time'],
                            'result': 'ERROR',
                            'test_id': line.split(' - ')[0] if ' - ' in line else 'UNKNOWN'
                        })
    
    if not data:
        # 데이터가 없는 경우 기본 그래프 생성
        fig = go.Figure()
        fig.add_annotation(
            text="시각화할 데이터가 없습니다",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False
        )
        return fig
    
    df = pd.DataFrame(data)
    df['execution_time'] = pd.to_datetime(df['execution_time'])
    df = df.sort_values('execution_time')
    
    # 결과별 카운트 계산
    result_counts = df.groupby(['execution_time', 'result']).size().unstack(fill_value=0)
    
    # 그래프 생성
    fig = go.Figure()
    
    # 각 결과별로 선 추가
    for result in ['PASS', 'FAIL', 'ERROR']:
        if result in result_counts.columns:
            fig.add_trace(go.Scatter(
                x=result_counts.index,
                y=result_counts[result],
                name=result,
                mode='lines+markers'
            ))
    
    # 레이아웃 설정
    fig.update_layout(
        title='테스트 실행 추이',
        xaxis_title='실행 시간',
        yaxis_title='실행 횟수',
        legend_title='결과',
        hovermode='x unified'
    )
    
    return fig

def calculate_coverage() -> Dict[str, float]:
    """테스트 커버리지를 계산합니다."""
    cases = load_all_cases()
    if not cases:
        return {"전체": 0.0}
    
    # 기능별 테스트 케이스 수 계산
    features = {}
    for case in cases:
        feature = case.get("feature", "기타")
        if feature not in features:
            features[feature] = 0
        features[feature] += 1
    
    # 전체 테스트 케이스 수
    total_cases = len(cases)
    
    # 커버리지 계산
    coverage = {
        feature: (count / total_cases * 100) 
        for feature, count in features.items()
    }
    coverage["전체"] = sum(coverage.values())
    
    return coverage

def analyze_failure_patterns() -> pd.DataFrame:
    """실패 패턴을 분석합니다."""
    history = load_test_history()
    if not history:
        return pd.DataFrame()
    
    # 실패한 테스트만 필터링
    failures = []
    for history_item in history:
        if history_item.get('type') == 'test_case':
            for result in history_item.get('results', []):
                if result.get('result') == 'FAIL':
                    failures.append({
                        'id': result.get('id', 'UNKNOWN'),
                        'desc': result.get('desc', 'N/A'),
                        'status_code': result.get('status_code', 'N/A'),
                        'reason': result.get('reason', 'N/A'),
                        'execution_time': history_item.get('execution_time', 'N/A'),
                        'env': history_item.get('env', 'N/A')
                    })
        elif history_item.get('type') == 'postman':
            postman_result = history_item.get('postman_result', {})
            if postman_result.get('status') == 'success':
                output_lines = postman_result.get('output', '').split('\n')
                for line in output_lines:
                    if '❌' in line:
                        # Postman 결과에서 실패 정보 추출
                        parts = line.split(' - ')
                        test_id = parts[0] if len(parts) > 0 else 'UNKNOWN'
                        test_desc = parts[1] if len(parts) > 1 else 'N/A'
                        failures.append({
                            'id': test_id,
                            'desc': test_desc,
                            'status_code': 'N/A',
                            'reason': 'Postman test failure',
                            'execution_time': history_item.get('execution_time', 'N/A'),
                            'env': history_item.get('env', 'N/A')
                        })
    
    if not failures:
        return pd.DataFrame()
    
    # 실패 패턴 분석
    patterns = []
    for failure in failures:
        pattern = {
            "테스트 ID": failure["id"],
            "설명": failure["desc"],
            "상태 코드": failure["status_code"],
            "실패 횟수": sum(1 for f in failures if f["id"] == failure["id"]),
            "마지막 실패": failure["execution_time"],
            "환경": failure["env"]
        }
        patterns.append(pattern)
    
    # DataFrame 생성 및 중복 제거
    df = pd.DataFrame(patterns)
    if not df.empty:
        df = df.drop_duplicates(subset=["테스트 ID"])
        df = df.sort_values("실패 횟수", ascending=False)
    
    return df

def plot_coverage(coverage_data: Dict[str, float]) -> alt.Chart:
    """테스트 커버리지를 시각화합니다."""
    # 데이터프레임 생성
    df = pd.DataFrame({
        '기능': list(coverage_data.keys()),
        '커버리지': list(coverage_data.values())
    })
    
    # 전체 커버리지 제외
    df = df[df['기능'] != '전체']
    
    # 차트 생성
    chart = alt.Chart(df).mark_bar().encode(
        x='기능',
        y='커버리지',
        color=alt.Color('커버리지', scale=alt.Scale(scheme='redyellowgreen', domain=[0, 100])),
        tooltip=['기능', '커버리지']
    ).properties(
        title='테스트 커버리지',
        width=600,
        height=400
    )
    
    return chart

def load_test_runs() -> List[str]:
    """테스트 실행 목록을 로드합니다."""
    test_runs = []
    results_dir = "results"
    
    if not os.path.exists(results_dir):
        return test_runs
    
    # 고유한 테스트 실행 ID 추출 (test_result_[ID].json 형식)
    run_files = {}
    for filename in os.listdir(results_dir):
        if filename.startswith("test_result_") and filename.endswith(".json"):
            try:
                # 파일 내용 읽기
                file_path = os.path.join(results_dir, filename)
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                # 결과 파일에 type 필드가 있는지 확인
                if "id" in data and "execution_time" in data:
                    run_id = data["id"]
                    execution_time = data["execution_time"]
                    
                    # type 필드 확인 (파일 형식이 다를 수 있음)
                    test_type = "unknown"
                    if "type" in data:  # 새로운 형식
                        test_type = data["type"]
                    elif "test_type" in data:  # 이전 형식
                        test_type = data["test_type"]
                    elif "results" in data and data["results"] and "test_type" in data["results"][0]:
                        # results 배열의 첫 번째 항목에서 test_type 확인
                        test_type = data["results"][0]["test_type"]
                    
                    # 사용자 친화적인 표현으로 변환
                    friendly_type = "AI 생성 테스트" if test_type == "ai_collection" else "Postman Collection" if test_type == "postman" else test_type
                    
                    # UI에 표시할 실행 정보 형식 지정
                    run_info = f"{run_id} - {execution_time} - 타입: {friendly_type}"
                    
                    # 중복 제거를 위해 사전에 저장
                    run_files[run_id] = run_info
            except Exception as e:
                print(f"Error loading test run file {filename}: {str(e)}")
    
    # 테스트 실행 목록 반환
    test_runs = list(run_files.values())
    return sorted(test_runs, reverse=True)

def find_result_file(run_id):
    """주어진 run_id에 해당하는 결과 파일을 찾습니다."""
    if not run_id:
        return None
    
    # 결과 파일 추정 패턴 목록
    file_patterns = [
        f"test_result_{run_id}.json",  # 정확한 ID 일치
        f"{run_id}.json"  # 간단한 ID만
    ]
    
    # results 디렉토리 확인
    results_dir = "results"
    if not os.path.exists(results_dir):
        return None
    
    # 패턴에 맞는 파일 찾기
    for pattern in file_patterns:
        file_path = os.path.join(results_dir, pattern)
        if os.path.exists(file_path):
            return file_path
    
    # 패턴 일치 파일이 없으면 부분 일치 검색
    for filename in os.listdir(results_dir):
        if filename.endswith(".json") and run_id in filename:
            # 파일 내용을 확인하여 올바른 run_id인지 검증
            try:
                file_path = os.path.join(results_dir, filename)
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    
                    # 메인 결과 파일 (테스트 실행 결과)
                    if "id" in data and data["id"] == run_id:
                        return file_path
                    
                    # 링크 파일 (테스트 케이스-실행 관계)
                    if "execution_id" in data and data["execution_id"] == run_id:
                        # 실제 실행 결과 파일 찾기
                        real_result_file = os.path.join(results_dir, f"test_result_{data['execution_id']}.json")
                        if os.path.exists(real_result_file):
                            return real_result_file
            except Exception as e:
                print(f"파일 검사 중 오류 {filename}: {str(e)}")
    
    # 파일을 찾지 못한 경우
    return None

def generate_comparison_report(selected_run, comparison_run):
    """두 테스트 실행 결과를 비교하여 보고서를 생성합니다."""
    report = []
    
    try:
        # 선택된 실행 결과 로드 (형식: "ID - 실행시간 - 타입: 타입명")
        parts = selected_run.split(" - ")
        run_id = parts[0] if parts else selected_run
        
        # 비교 대상 실행 결과 로드
        comparison_parts = comparison_run.split(" - ") if comparison_run else []
        comparison_id = comparison_parts[0] if comparison_parts else comparison_run
        
        # 현재 결과 파일 찾기
        result_file = find_result_file(run_id)
        
        # 비교 결과 파일 찾기
        comparison_file = find_result_file(comparison_id) if comparison_id else None
        
        if not result_file:
            print(f"결과 파일을 찾을 수 없음: {run_id}")
            return None
            
        if comparison_id and not comparison_file:
            print(f"비교 결과 파일을 찾을 수 없음: {comparison_id}")
            return None
        
        with open(result_file, "r", encoding="utf-8") as f:
            current_data = json.load(f)
        
        comparison_data = None
        if comparison_file:
            with open(comparison_file, "r", encoding="utf-8") as f:
                comparison_data = json.load(f)
        
        # 테스트 타입이 다른 경우 비교할 수 없음
        if comparison_data and current_data.get("type") != comparison_data.get("type"):
            report.append("# ⚠️ 테스트 결과 비교 불가\n")
            report.append(f"선택한 두 테스트 결과의 유형이 서로 다릅니다.\n")
            report.append(f"- 기준 실행 유형: {current_data.get('type', 'N/A')}")
            report.append(f"- 비교 대상 유형: {comparison_data.get('type', 'N/A')}\n")
            report.append("서로 같은 유형의 테스트 결과만 비교할 수 있습니다.")
            return "\n".join(report)
        
        # 보고서 헤더
        report.append("# 테스트 결과 비교 보고서\n")
        
        # 실행 정보
        report.append(f"## 실행 정보\n")
        report.append(f"### 기준 실행")
        report.append(f"- 실행 ID: {current_data['id']}")
        report.append(f"- 실행 시간: {current_data['execution_time']}")
        report.append(f"- 테스트 환경: {current_data.get('env', 'N/A')}")
        report.append(f"- 테스트 타입: {current_data.get('type', 'N/A')}\n")
        
        if comparison_data:
            report.append(f"### 비교 대상 실행")
            report.append(f"- 실행 ID: {comparison_data['id']}")
            report.append(f"- 실행 시간: {comparison_data['execution_time']}")
            report.append(f"- 테스트 환경: {comparison_data.get('env', 'N/A')}")
            report.append(f"- 테스트 타입: {comparison_data.get('type', 'N/A')}\n")
        
        # 결과 비교 요약
        report.append(f"## 비교 요약\n")
        
        if current_data.get("type") == "postman" and (not comparison_data or comparison_data.get("type") == "postman"):
            # Postman 결과 비교
            current_result = current_data.get("postman_result", {})
            comparison_result = comparison_data.get("postman_result", {}) if comparison_data else None
            
            if current_result.get("status") == "success":
                # 현재 실행 결과 요약 추출 및 분석
                current_total_count = 0
                current_success_count = 0
                current_fail_count = 0
                current_warning_count = 0
                
                # raw_result로부터 실제 요청 결과 분석
                if 'raw_result' in current_result and 'run' in current_result['raw_result']:
                    executions = current_result['raw_result']['run'].get('executions', [])
                    current_total_count = len(executions)
                    
                    for execution in executions:
                        response = execution.get('response', {})
                        status_code = response.get('code', 0)
                        
                        # 상태 코드로 성공/실패 판단
                        if 200 <= status_code < 300:
                            current_success_count += 1
                        elif status_code >= 400:
                            current_fail_count += 1
                        else:
                            current_warning_count += 1
                
                # 비교 실행 결과 요약 추출 및 분석
                comparison_total_count = 0
                comparison_success_count = 0
                comparison_fail_count = 0
                comparison_warning_count = 0
                
                if comparison_result and comparison_result.get("status") == "success":
                    if 'raw_result' in comparison_result and 'run' in comparison_result['raw_result']:
                        executions = comparison_result['raw_result']['run'].get('executions', [])
                        comparison_total_count = len(executions)
                        
                        for execution in executions:
                            response = execution.get('response', {})
                            status_code = response.get('code', 0)
                            
                            # 상태 코드로 성공/실패 판단
                            if 200 <= status_code < 300:
                                comparison_success_count += 1
                            elif status_code >= 400:
                                comparison_fail_count += 1
                            else:
                                comparison_warning_count += 1
                
                # 결과 요약 비교 표시
                report.append("### Postman 테스트 결과 비교")
                report.append(f"| 지표 | 기준 실행 | 비교 대상 | 차이 |")
                report.append(f"| --- | --- | --- | --- |")
                report.append(f"| 총 요청 수 | {current_total_count} | {comparison_total_count} | {current_total_count - comparison_total_count} |")
                report.append(f"| 성공 | {current_success_count} | {comparison_success_count} | {current_success_count - comparison_success_count} |")
                report.append(f"| 실패 | {current_fail_count} | {comparison_fail_count} | {current_fail_count - comparison_fail_count} |")
                report.append(f"| 경고 | {current_warning_count} | {comparison_warning_count} | {current_warning_count - comparison_warning_count} |")
                
                success_rate_current = (current_success_count / current_total_count * 100) if current_total_count > 0 else 0
                success_rate_comparison = (comparison_success_count / comparison_total_count * 100) if comparison_total_count > 0 else 0
                
                report.append(f"| 성공률 | {success_rate_current:.1f}% | {success_rate_comparison:.1f}% | {success_rate_current - success_rate_comparison:.1f}% |")
                report.append("")
                
                # 상세 비교 결과
                report.append(f"## 상세 비교 결과\n")
                
                # Postman 요청 추출 (현재)
                current_requests = {}
                if 'raw_result' in current_result and 'run' in current_result['raw_result']:
                    executions = current_result['raw_result']['run'].get('executions', [])
                    for execution in executions:
                        item = execution.get('item', {})
                        request = execution.get('request', {})
                        response = execution.get('response', {})
                        
                        method = request.get('method', '')
                        path = '/'.join(request.get('url', {}).get('path', []))
                        name = item.get('name', f"{method} {path}")
                        status_code = response.get('code', 0)
                        
                        status = "성공" if 200 <= status_code < 300 else "실패" if status_code >= 400 else "경고"
                        current_requests[name] = {
                            "status": status,
                            "status_code": status_code
                        }
                
                # Postman 요청 추출 (비교)
                comparison_requests = {}
                if comparison_result and comparison_result.get("status") == "success":
                    if 'raw_result' in comparison_result and 'run' in comparison_result['raw_result']:
                        executions = comparison_result['raw_result']['run'].get('executions', [])
                        for execution in executions:
                            item = execution.get('item', {})
                            request = execution.get('request', {})
                            response = execution.get('response', {})
                            
                            method = request.get('method', '')
                            path = '/'.join(request.get('url', {}).get('path', []))
                            name = item.get('name', f"{method} {path}")
                            status_code = response.get('code', 0)
                            
                            status = "성공" if 200 <= status_code < 300 else "실패" if status_code >= 400 else "경고"
                            comparison_requests[name] = {
                                "status": status,
                                "status_code": status_code
                            }
                
                # 상태가 변경된 요청만 표시
                report.append("### 상태가 변경된 요청")
                
                if comparison_requests:
                    status_changed = False
                    for name, current_info in current_requests.items():
                        if name in comparison_requests and current_info["status"] != comparison_requests[name]["status"]:
                            status_changed = True
                            old_status = comparison_requests[name]["status"]
                            new_status = current_info["status"]
                            old_code = comparison_requests[name]["status_code"]
                            new_code = current_info["status_code"]
                            
                            report.append(f"#### {name}")
                            report.append(f"- 이전 상태: {old_status} (상태 코드: {old_code})")
                            report.append(f"- 현재 상태: {new_status} (상태 코드: {new_code})")
                            report.append("")
                    
                    if not status_changed:
                        report.append("변경된 요청이 없습니다.\n")
                else:
                    report.append("비교 대상이 없습니다.\n")
                
                # 신규 요청 표시
                report.append("### 신규 추가된 요청")
                new_requests = [name for name in current_requests.keys() if name not in comparison_requests]
                
                if new_requests:
                    for name in new_requests:
                        info = current_requests[name]
                        report.append(f"- {name}: {info['status']} (상태 코드: {info['status_code']})")
                    report.append("")
                else:
                    report.append("신규 추가된 요청이 없습니다.\n")
                
                # 삭제된 요청 표시
                report.append("### 삭제된 요청")
                removed_requests = [name for name in comparison_requests.keys() if name not in current_requests]
                
                if removed_requests:
                    for name in removed_requests:
                        info = comparison_requests[name]
                        report.append(f"- {name}: {info['status']} (상태 코드: {info['status_code']})")
                    report.append("")
                else:
                    report.append("삭제된 요청이 없습니다.\n")
            
        elif current_data.get("type") in ["test_case", "ai_collection"] and (not comparison_data or comparison_data.get("type") in ["test_case", "ai_collection"]):
            # 테스트 케이스 결과 비교
            current_results = current_data.get("results", [])
            comparison_results = comparison_data.get("results", []) if comparison_data else []
            
            # 현재 결과 요약
            current_success_count = sum(1 for r in current_results if r.get("result") == "PASS")
            current_fail_count = sum(1 for r in current_results if r.get("result") == "FAIL")
            current_warning_count = sum(1 for r in current_results if r.get("result") == "ERROR")
            current_total_count = len(current_results)
            
            # 비교 결과 요약
            comparison_success_count = sum(1 for r in comparison_results if r.get("result") == "PASS")
            comparison_fail_count = sum(1 for r in comparison_results if r.get("result") == "FAIL")
            comparison_warning_count = sum(1 for r in comparison_results if r.get("result") == "ERROR")
            comparison_total_count = len(comparison_results)
            
            # 결과 요약 비교 표시
            report.append("### 테스트 케이스 결과 비교")
            report.append(f"| 지표 | 기준 실행 | 비교 대상 | 차이 |")
            report.append(f"| --- | --- | --- | --- |")
            report.append(f"| 총 테스트 케이스 | {current_total_count} | {comparison_total_count} | {current_total_count - comparison_total_count} |")
            report.append(f"| 성공 | {current_success_count} | {comparison_success_count} | {current_success_count - comparison_success_count} |")
            report.append(f"| 실패 | {current_fail_count} | {comparison_fail_count} | {current_fail_count - comparison_fail_count} |")
            report.append(f"| 오류 | {current_warning_count} | {comparison_warning_count} | {current_warning_count - comparison_warning_count} |")
            
            success_rate_current = (current_success_count / current_total_count * 100) if current_total_count > 0 else 0
            success_rate_comparison = (comparison_success_count / comparison_total_count * 100) if comparison_total_count > 0 else 0
            
            report.append(f"| 성공률 | {success_rate_current:.1f}% | {success_rate_comparison:.1f}% | {success_rate_current - success_rate_comparison:.1f}% |")
            report.append("")
            
            # 상세 비교 결과
            report.append(f"## 상세 비교 결과\n")
            
            # ID별 테스트 케이스 결과 매핑
            current_result_map = {r.get("id"): r for r in current_results}
            comparison_result_map = {r.get("id"): r for r in comparison_results}
            
            # 상태가 변경된 테스트 케이스 표시
            report.append("### 상태가 변경된 테스트 케이스")
            
            status_changed = False
            for test_id, current_result in current_result_map.items():
                if test_id in comparison_result_map and current_result.get("result") != comparison_result_map[test_id].get("result"):
                    status_changed = True
                    old_status = comparison_result_map[test_id].get("result")
                    new_status = current_result.get("result")
                    
                    report.append(f"#### {test_id} - {current_result.get('desc', 'No Description')}")
                    report.append(f"- 이전 상태: {old_status}")
                    report.append(f"- 현재 상태: {new_status}")
                    
                    # 실패 이유 표시
                    if new_status == "FAIL":
                        report.append("\n**실패 사유:**")
                        report.append(f"```\n{current_result.get('error', 'No error details')}\n```")
                    elif new_status == "ERROR":
                        report.append("\n**오류 사유:**")
                        report.append(f"```\n{current_result.get('reason', 'No reason details')}\n```")
                    
                    report.append("")
            
            if not status_changed:
                report.append("변경된 테스트 케이스가 없습니다.\n")
            
            # 신규 테스트 케이스 표시
            report.append("### 신규 추가된 테스트 케이스")
            new_tests = [test_id for test_id in current_result_map.keys() if test_id not in comparison_result_map]
            
            if new_tests:
                for test_id in new_tests:
                    result = current_result_map[test_id]
                    status = result.get("result")
                    report.append(f"- {test_id} - {result.get('desc', 'No Description')}: {status}")
                report.append("")
            else:
                report.append("신규 추가된 테스트 케이스가 없습니다.\n")
            
            # 삭제된 테스트 케이스 표시
            report.append("### 삭제된 테스트 케이스")
            removed_tests = [test_id for test_id in comparison_result_map.keys() if test_id not in current_result_map]
            
            if removed_tests:
                for test_id in removed_tests:
                    result = comparison_result_map[test_id]
                    status = result.get("result")
                    report.append(f"- {test_id} - {result.get('desc', 'No Description')}: {status}")
                report.append("")
            else:
                report.append("삭제된 테스트 케이스가 없습니다.\n")
        
        return "\n".join(report)
    
    except Exception as e:
        import traceback
        print(f"비교 보고서 생성 중 오류 발생: {str(e)}")
        print(traceback.format_exc())
        
        # 간단한 오류 보고서 생성
        error_report = []
        error_report.append("# ⚠️ 비교 보고서 생성 중 오류 발생\n")
        error_report.append(f"## 오류 정보\n")
        error_report.append(f"- 기준 실행 ID: {selected_run}")
        error_report.append(f"- 비교 실행 ID: {comparison_run}")
        error_report.append(f"- 오류 메시지: {str(e)}\n")
        
        return "\n".join(error_report)

def generate_test_report(selected_run, result_file_path=None):
    """테스트 실행 결과에 대한 보고서를 생성합니다."""
    report = []
    
    try:
        # 선택된 실행 결과 로드
        run_id = selected_run.split(" - ")[0]
        
        # 결과 파일 경로 (직접 전달된 경우 우선 사용)
        if result_file_path and os.path.exists(result_file_path):
            result_file = result_file_path
        else:
            # find_result_file 함수를 사용하여 파일 찾기
            result_file = find_result_file(run_id)
        
        print(f"보고서 생성 시도: {result_file}")
        
        if not result_file or not os.path.exists(result_file):
            print(f"결과 파일을 찾을 수 없음: {run_id}")
            return None
        
        with open(result_file, "r", encoding="utf-8") as f:
            result_data = json.load(f)
            print(f"결과 데이터 타입: {result_data.get('type', 'unknown')}")
        
        # 필수 필드 확인
        if 'id' not in result_data or 'execution_time' not in result_data:
            print(f"필수 필드 누락: id 또는 execution_time")
            return None
        
        # 보고서 헤더
        report.append("# 테스트 실행 보고서\n")
        report.append(f"## 실행 정보\n")
        report.append(f"- 실행 ID: {result_data.get('id', 'N/A')}")
        report.append(f"- 실행 시간: {result_data.get('execution_time', 'N/A')}")
        report.append(f"- 테스트 환경: {result_data.get('env', 'N/A')}")
        
        # test_type 필드 확인
        test_type = None
        
        # 1. 직접 'type' 필드 확인 (새로운 형식)
        if "type" in result_data:
            test_type = result_data["type"]
        # 2. 'test_type' 필드 확인 (이전 형식)
        elif "test_type" in result_data:
            test_type = result_data["test_type"]
        # 3. results 배열에서 확인
        elif "results" in result_data and result_data["results"]:
            first_result = result_data["results"][0]
            if "test_type" in first_result:
                test_type = first_result["test_type"]
        
        # 기본값 설정
        if not test_type:
            test_type = "unknown"
        
        # 테스트 유형 표시 (사용자 친화적인 형태로)
        friendly_type = "AI 생성 테스트" if test_type == "ai_collection" else "Postman Collection" if test_type == "postman" else test_type
        report.append(f"- 테스트 타입: {friendly_type}\n")
        
        # 테스트 타입별 처리를 위해 필요
        if test_type == "postman":
            if "postman_result" not in result_data:
                print("Postman 결과 누락")
                return None
                
            result = result_data["postman_result"]
            if result.get("status") == "success":
                # Postman 결과 분석
                output_lines = result.get("output", "").split('\n')
                
                # 결과 요약 추출
                total_count = 0
                success_count = 0
                fail_count = 0
                warning_count = 0
                
                for line in output_lines:
                    if "총 요청 수:" in line:
                        try:
                            total_count = int(line.split(":")[1].strip())
                        except (ValueError, IndexError):
                            pass
                    elif "성공:" in line:
                        try:
                            success_count = int(line.split(":")[1].strip())
                        except (ValueError, IndexError):
                            pass
                    elif "실패:" in line:
                        try:
                            fail_count = int(line.split(":")[1].strip())
                        except (ValueError, IndexError):
                            pass
                
                # 결과 요약
                report.append(f"## 테스트 결과 요약\n")
                report.append(f"- 총 요청 수: {total_count}")
                report.append(f"- 성공: {success_count}")
                report.append(f"- 실패: {fail_count}")
                report.append(f"- 경고: {warning_count}\n")
                
                # 상세 결과
                report.append(f"## 상세 결과\n")
                
                # raw_result에서 실행 정보 추출
                if 'raw_result' in result and 'run' in result['raw_result']:
                    executions = result['raw_result']['run'].get('executions', [])
                    for execution in executions:
                        item = execution.get('item', {})
                        request = execution.get('request', {})
                        response = execution.get('response', {})
                        
                        # 요청 정보
                        method = request.get('method', '')
                        url = request.get('url', {})
                        host = url.get('host', [''])[0] if isinstance(url.get('host', []), list) and url.get('host', []) else ''
                        port = url.get('port', '')
                        path = '/'.join(url.get('path', [])) if isinstance(url.get('path', []), list) else ''
                        full_url = f"http://{host}:{port}/{path}"
                        
                        # 요청 본문
                        request_body = request.get('body', {}).get('raw', '') if isinstance(request.get('body', {}), dict) else ''
                        
                        # 응답 정보
                        response_code = response.get('code', '')
                        response_body = ''
                        if 'stream' in response and 'data' in response['stream']:
                            try:
                                response_body = bytes(response['stream']['data']).decode('utf-8')
                            except:
                                response_body = str(response['stream']['data'])
                        
                        # 보고서에 추가
                        report.append(f"### {method} - {item.get('name', '')}")
                        report.append(f"**Endpoint**: {full_url}")
                        report.append(f"**Status Code**: {response_code}")
                        
                        if request_body:
                            report.append("\n**Request Body**:")
                            report.append(f"```json\n{request_body}\n```")
                        
                        if response_body:
                            report.append("\n**Response Body**:")
                            report.append(f"```json\n{response_body}\n```")
                        
                        report.append("")  # 각 요청 사이에 빈 줄 추가
        elif test_type in ["test_case", "ai_collection"]:  # test_case 또는 ai_collection 타입
            # 테스트 케이스 결과 처리
            if "results" not in result_data:
                print(f"'{test_type}' 타입이지만 results 필드 누락")
                if test_type == "ai_collection":
                    # 간단한 보고서라도 생성
                    report.append(f"## AI 생성 테스트 결과\n")
                    report.append(f"테스트 ID: {result_data.get('id', 'N/A')}")
                    report.append(f"실행 시간: {result_data.get('execution_time', 'N/A')}")
                    return "\n".join(report)
                return None
                
            results = result_data.get("results", [])
            if not results:
                print(f"'{test_type}' 타입이지만 results가 비어 있음")
                return None
            
            # 결과 요약
            success_count = sum(1 for r in results if r.get("result") == "PASS")
            fail_count = sum(1 for r in results if r.get("result") == "FAIL")
            warning_count = sum(1 for r in results if r.get("result") == "ERROR")
            total_count = len(results)
            
            report.append(f"## 테스트 결과 요약\n")
            report.append(f"- 총 테스트 케이스: {total_count}")
            report.append(f"- 성공: {success_count}")
            report.append(f"- 실패: {fail_count}")
            report.append(f"- 오류: {warning_count}\n")
            
            # 상세 결과
            report.append(f"## 상세 결과\n")
            for result in results:
                result_type = result.get("result", "UNKNOWN")
                result_id = result.get("id", "ID 없음")
                result_desc = result.get("desc", "설명 없음")
                
                if result_type == "PASS":
                    report.append(f"### ✅ {result_id} - {result_desc}")
                    if "body" in result:
                        body_content = json.dumps(result["body"], ensure_ascii=False, indent=2) if isinstance(result["body"], (dict, list)) else str(result["body"])
                        report.append(f"\n```json\n{body_content}\n```")
                elif result_type == "FAIL":
                    report.append(f"### ❌ {result_id} - {result_desc}")
                    if "body" in result:
                        body_content = json.dumps(result["body"], ensure_ascii=False, indent=2) if isinstance(result["body"], (dict, list)) else str(result["body"])
                        report.append(f"\n```json\n{body_content}\n```")
                else:
                    report.append(f"### ⚠️ {result_id} - {result_desc}")
                    if "reason" in result:
                        report.append(f"\n{result['reason']}")
                report.append("")  # 각 결과 사이에 빈 줄 추가
        else:
            print(f"지원하지 않는 테스트 타입: {test_type}")
            report.append(f"## 오류\n")
            report.append(f"지원하지 않는 테스트 타입: {test_type}")
            return "\n".join(report)
        
        return "\n".join(report)
        
    except Exception as e:
        import traceback
        print(f"보고서 생성 중 오류 발생: {str(e)}")
        print(traceback.format_exc())
        
        # 간단한 오류 보고서 생성
        error_report = []
        error_report.append("# ⚠️ 보고서 생성 중 오류 발생\n")
        error_report.append(f"## 오류 정보\n")
        error_report.append(f"- 실행 ID: {selected_run}")
        error_report.append(f"- 오류 메시지: {str(e)}\n")
        
        return "\n".join(error_report)

def load_test_result(run_id: str) -> Optional[Dict[str, Any]]:
    """특정 테스트 실행 결과를 로드합니다."""
    try:
        # run_id에서 실제 ID 추출 (예: "test_id - 2024-03-21 14:30:00" -> "test_id")
        actual_id = run_id.split(" - ")[0] if " - " in run_id else run_id
        
        # find_result_file 함수를 사용하여 파일 찾기
        result_file = find_result_file(actual_id)
        
        if not result_file:
            print(f"결과 파일을 찾을 수 없습니다: {actual_id}")
            return None
        
        with open(result_file, "r", encoding="utf-8") as f:
            result = json.load(f)
            
            # 결과 타입이 없는 경우 추가
            if 'type' not in result:
                if 'postman_result' in result:
                    result['type'] = 'postman'
                else:
                    result['type'] = 'test_case'
            
            return result
    except Exception as e:
        print(f"테스트 결과 로드 중 오류 발생: {str(e)}")
        return None

if __name__ == "__main__":
    run_and_report()