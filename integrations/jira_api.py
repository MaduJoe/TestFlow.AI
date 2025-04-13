import requests
from requests.auth import HTTPBasicAuth
import json
import os
from dotenv import load_dotenv
import datetime

# .env 파일에서 환경 변수 로드
load_dotenv()

class JiraAPI:
    """Jira API와 통합하기 위한 클래스"""
    
    def __init__(self, domain=None, email=None, api_token=None):
        """
        Jira API 클라이언트 초기화
        
        Args:
            domain: Jira 도메인 (예: 'https://your-domain.atlassian.net')
            email: Jira 계정 이메일
            api_token: Jira API 토큰
        """
        # 인자가 제공되지 않으면 환경 변수에서 로드
        self.domain = domain or os.getenv('JIRA_DOMAIN')
        self.email = email or os.getenv('JIRA_EMAIL')
        self.api_token = api_token or os.getenv('JIRA_API_TOKEN')
        
        if not all([self.domain, self.email, self.api_token]):
            raise ValueError("Jira 도메인, 이메일, API 토큰이 필요합니다. 인자로 제공하거나 환경 변수를 설정하세요.")
        
        # 기본 인증 (사용자명 + API 토큰)
        self.auth = HTTPBasicAuth(self.email, self.api_token)
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
    
    def test_connection(self):
        """Jira API 연결 테스트"""
        try:
            response = requests.get(self.domain, headers=self.headers, auth=self.auth)
            return {
                "status_code": response.status_code,
                "success": 200 <= response.status_code < 300,
                "message": "연결 성공" if 200 <= response.status_code < 300 else f"연결 실패: {response.text}"
            }
        except Exception as e:
            return {
                "status_code": None,
                "success": False,
                "message": f"연결 실패: {str(e)}"
            }
    
    def create_issue(self, project_key, summary, description, issue_type="Bug"):
        """
        Jira 이슈 생성
        
        Args:
            project_key: 프로젝트 키
            summary: 이슈 제목
            description: 이슈 설명
            issue_type: 이슈 유형 (기본값: Bug)
            
        Returns:
            생성된 이슈 정보 또는 오류 메시지
        """
        # Jira Cloud
        url = f"{self.domain}/rest/api/3/issue"
        
        # Jira Server/Data Center (API 버전 2)
        url = f"{self.domain}/rest/api/2/issue"
        
        payload = json.dumps({
            "fields": {
                "project": {
                    "key": project_key
                },
                "summary": summary,
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "type": "text",
                                    "text": description
                                }
                            ]
                        }
                    ]
                },
                "issuetype": {
                    "name": issue_type
                }
            }
        })
        
        try:
            response = requests.post(url, json=payload, headers=self.headers, auth=self.auth)
            if 200 <= response.status_code < 300:
                return {
                    "success": True,
                    "issue_key": response.json().get("key"),
                    "issue_id": response.json().get("id"),
                    "issue_url": f"{self.domain}/browse/{response.json().get('key')}"
                }
            else:
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "message": response.text
                }
        except Exception as e:
            return {
                "success": False,
                "message": str(e)
            }
    
    def get_project_info(self, project_key):
        """
        프로젝트 정보 조회
        
        Args:
            project_key: 프로젝트 키
            
        Returns:
            프로젝트 정보 또는 오류 메시지
        """
        url = f"{self.domain}/rest/api/3/project/{project_key}"
        
        try:
            response = requests.get(url, headers=self.headers, auth=self.auth)
            if 200 <= response.status_code < 300:
                return {
                    "success": True,
                    "project_info": response.json()
                }
            else:
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "message": response.text
                }
        except Exception as e:
            return {
                "success": False,
                "message": str(e)
            }
    
    def get_issue_types(self):
        """
        Jira에서 사용 가능한 이슈 유형 목록을 조회합니다.
        
        Returns:
            사용 가능한 이슈 유형 목록 또는 오류 메시지
        """
        url = f"{self.domain}/rest/api/2/issuetype"
        
        try:
            response = requests.get(url, headers=self.headers, auth=self.auth)
            if 200 <= response.status_code < 300:
                return {
                    "success": True,
                    "issue_types": response.json()
                }
            else:
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "message": response.text
                }
        except Exception as e:
            return {
                "success": False,
                "message": str(e)
            }
    
    def get_project_issue_types(self, project_key):
        """
        특정 프로젝트에서 사용 가능한 이슈 유형 목록을 조회합니다.
        
        Args:
            project_key: 프로젝트 키
            
        Returns:
            프로젝트에서 사용 가능한 이슈 유형 목록 또는 오류 메시지
        """
        # 프로젝트 메타데이터 조회
        url = f"{self.domain}/rest/api/2/issue/createmeta?projectKeys={project_key}&expand=projects.issuetypes"
        
        try:
            response = requests.get(url, headers=self.headers, auth=self.auth)
            if 200 <= response.status_code < 300:
                data = response.json()
                # 프로젝트 검색
                projects = data.get("projects", [])
                for project in projects:
                    if project.get("key") == project_key:
                        # 프로젝트의 이슈 유형 목록 반환
                        return {
                            "success": True,
                            "issue_types": project.get("issuetypes", [])
                        }
                
                # 프로젝트를 찾지 못한 경우
                return {
                    "success": False,
                    "message": f"프로젝트 {project_key}를 찾을 수 없습니다."
                }
            else:
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "message": response.text
                }
        except Exception as e:
            return {
                "success": False,
                "message": str(e)
            }
    
    def create_test_issue_from_failed_test(self, test_result, project_key):
        """
        실패한 테스트 결과를 기반으로 Jira 이슈 생성
        
        Args:
            test_result: 테스트 결과 데이터
            project_key: 프로젝트 키
            
        Returns:
            생성된 이슈 정보 또는 오류 메시지
        """
        if isinstance(test_result, dict):
            # 테스트 케이스 실패 정보 추출
            test_id = test_result.get('id', 'Unknown Test')
            description = test_result.get('desc', 'No description')
            error = test_result.get('error', test_result.get('reason', 'Unknown error'))
            body = test_result.get('body', '')
            timestamp = test_result.get('timestamp', datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
            # created_at = test_result.get('created_at', datetime.datetime.now().isoformat())
            
            # 이슈 제목 및 설명 구성
            summary = f"테스트 케이스 실패: {test_id}"
            # issue_description = f"{description}\n\n결과: {test_result.get('result', 'FAIL')}\n이유: {error}\n타임스탬프: {timestamp}\n생성일: {created_at}\n상태: OPEN"
            issue_description = f"{description}\n\n결과: {test_result.get('result', 'FAIL')}\n이유: {error}\n타임스탬프: {timestamp}\n상태: OPEN"
            
            # 프로젝트에서 사용 가능한 이슈 유형 조회
            project_issue_types_result = self.get_project_issue_types(project_key)
            
            if not project_issue_types_result.get("success"):
                print(f"프로젝트 이슈 유형 조회 실패: {project_issue_types_result.get('message')}")
                # 일반 이슈 유형 조회로 대체
                issue_types_result = self.get_issue_types()
                
                if not issue_types_result.get("success"):
                    return {
                        "success": False,
                        "message": f"이슈 유형 조회 실패: {issue_types_result.get('message')}"
                    }
                
                issue_types = issue_types_result.get("issue_types", [])
            else:
                issue_types = project_issue_types_result.get("issue_types", [])
                print(f"프로젝트 {project_key}에서 사용 가능한 이슈 유형: {[it.get('name') for it in issue_types]}")
            
            # 하위 작업(Sub-task)이 아닌 이슈 유형만 필터링
            standard_issue_types = [it for it in issue_types if not it.get("subtask", False)]
            
            # 일반 이슈 유형이 없으면 전체 목록 사용
            if not standard_issue_types:
                standard_issue_types = issue_types
            
            # 버그 유형 찾기 (Bug 또는 결함 등의 이름으로 존재할 수 있음)
            bug_issue_type = None
            bug_keywords = ["bug", "버그", "결함", "오류", "defect", "task", "task", "작업"]
            
            for issue_type in standard_issue_types:
                # 이슈 유형 이름에 bug 키워드가 포함되어 있는지 확인
                name = issue_type.get("name", "").lower()
                for keyword in bug_keywords:
                    if keyword in name:
                        bug_issue_type = issue_type
                        break
                if bug_issue_type:
                    break
            
            # 버그 유형을 찾지 못한 경우 첫 번째 일반 이슈 유형 사용
            if not bug_issue_type and standard_issue_types:
                bug_issue_type = standard_issue_types[0]
            
            # 이슈 유형을 찾지 못한 경우 에러 반환
            if not bug_issue_type:
                return {
                    "success": False,
                    "message": "사용 가능한 이슈 유형이 없습니다."
                }
            
            # 디버깅 정보 출력
            print(f"선택된 이슈 유형: {bug_issue_type.get('name')} (ID: {bug_issue_type.get('id')})")
            
            # Jira REST API 페이로드
            url = f"{self.domain}/rest/api/2/issue"
            
            payload = {
                "fields": {
                    "project": {
                        "key": project_key
                    },
                    "summary": summary,
                    "description": issue_description,
                    "issuetype": {
                        "id": bug_issue_type.get("id")
                    }
                }
            }
            
            try:
                response = requests.post(url, json=payload, headers=self.headers, auth=self.auth)
                if 200 <= response.status_code < 300:
                    return {
                        "success": True,
                        "issue_key": response.json().get("key"),
                        "issue_id": response.json().get("id"),
                        "issue_url": f"{self.domain}/browse/{response.json().get('key')}"
                    }
                else:
                    return {
                        "success": False,
                        "status_code": response.status_code,
                        "message": response.text
                    }
            except Exception as e:
                return {
                    "success": False,
                    "message": str(e)
                }
        else:
            return {
                "success": False,
                "message": "Invalid test result data"
            }


# 테스트 코드
if __name__ == "__main__":
    # 환경 변수에서 인증 정보를 로드하거나 직접 지정할 수 있습니다.
    jira = JiraAPI(
        # 아래 정보를 직접 입력하거나 .env 파일에 저장하세요
        # domain="https://your-domain.atlassian.net",
        # email="your-email@example.com",
        # api_token="your-api-token"
    )
    
    # 연결 테스트
    connection_test = jira.test_connection()
    print(f"Jira 연결 상태: {connection_test['message']}")
    
    if connection_test["success"]:
        # 여기에 추가 테스트 코드를 작성할 수 있습니다
        # 예: 프로젝트 정보 조회
        # project_info = jira.get_project_info("PROJECT_KEY")
        # print(project_info)
        pass

    # 프로젝트 정보 가져오기 (읽기 전용 작업으로 테스트)
    test_url = f"{jira.domain}/rest/api/2/project/{project_key}"
    response = requests.get(test_url, auth=jira.auth)
    print(response.status_code)
