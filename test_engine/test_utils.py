import requests
import json

def run_test_case(case):
    try:
        response = requests.request(
            method=case["method"],
            url=case["url"],
            headers=case.get("headers", {}),
            json=case.get("body", None)
        )
        status_pass = response.status_code == case["expected_status"]
        body_pass = case["expected_keyword"] in response.text
        passed = status_pass and body_pass

        return {
            "id": case["id"],
            "desc": case["description"],
            "status": response.status_code,
            "body": response.text,
            "result": "PASS" if passed else "FAIL",
            "reason": "" if passed else "Unexpected response"
        }

    except Exception as e:
        return {
            "id": case["id"],
            "desc": case["description"],
            "status": "ERROR",
            "body": str(e),
            "result": "ERROR",
            "reason": "Exception occurred"
        }
