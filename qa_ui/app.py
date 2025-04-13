import sys
import os

# 프로젝트 루트 디렉토리를 Python 경로에 추가 - test_engine import 전에 실행
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from datetime import datetime
import json
import pandas as pd
from io import BytesIO
import pdfkit
import base64
import markdown2
import streamlit as st
from test_engine.test_runner import (
    load_all_cases,
    run_test_case,
    run_selected_cases,
    load_test_history,
    filter_cases,
    group_cases_by_feature,
    update_case_priority,
    delete_case,
    plot_test_trend,
    calculate_coverage,
    analyze_failure_patterns,
    plot_coverage,
    load_test_runs,
    generate_test_report,
    generate_comparison_report,
    create_issue_file
)
from test_engine.postman_runner import run_postman_collection
from test_engine.test_case_generator import TestCaseGenerator
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import threading
import time
from integrations.jira_api import JiraAPI

# 페이지 설정
st.set_page_config(
    page_title="TestFlow AI",
    page_icon="🔍",
    layout="wide"
)

# 세션 상태 초기화
if 'postman_result' not in st.session_state:
    st.session_state.postman_result = None
if 'postman_success_count' not in st.session_state:
    st.session_state.postman_success_count = 0
if 'postman_fail_count' not in st.session_state:
    st.session_state.postman_fail_count = 0
if 'postman_warning_count' not in st.session_state:
    st.session_state.postman_warning_count = 0
if 'test_case_success_count' not in st.session_state:
    st.session_state.test_case_success_count = 0
if 'test_case_fail_count' not in st.session_state:
    st.session_state.test_case_fail_count = 0
if 'test_case_warning_count' not in st.session_state:
    st.session_state.test_case_warning_count = 0
if 'test_case_result' not in st.session_state:
    st.session_state.test_case_result = None
if 'last_test_time' not in st.session_state:
    st.session_state.last_test_time = None
if 'test_type' not in st.session_state:
    st.session_state.test_type = None

# 가장 최근 테스트 실행 정보 로드
if not st.session_state.last_test_time:
    test_runs = load_test_runs()
    if test_runs:
        latest_run = test_runs[0]  # 가장 최근 실행
        run_id = latest_run.split(" - ")[0]
        result_file = os.path.join("results", f"test_result_{run_id}.json")
        
        if os.path.exists(result_file):
            with open(result_file, "r", encoding="utf-8") as f:
                result_data = json.load(f)
                st.session_state.last_test_time = datetime.strptime(result_data["execution_time"], "%Y-%m-%d %H:%M:%S")
                st.session_state.test_type = result_data["type"]
                
                if result_data["type"] == "postman":
                    st.session_state.postman_result = result_data["postman_result"]
                else:
                    st.session_state.test_case_result = result_data["results"]

# 스케줄러 초기화
scheduler = BackgroundScheduler()
scheduler.start()

def run_scheduled_test():
    """매주 토요일 14시에 실행될 테스트 함수"""
    try:
        # 모든 테스트 케이스 로드
        cases = load_all_cases()
        if not cases:
            print("실행할 테스트 케이스가 없습니다.")
            return
            
        # 모든 테스트 케이스 선택
        selected_cases = [f"{case['id']} - {case['title']}" for case in cases]
        
        # 테스트 실행
        results = run_selected_cases(selected_cases, "dev")  # 기본적으로 개발 환경에서 실행
        
        # 결과 저장
        result_data = {
            "id": datetime.now().strftime("%Y%m%d%H%M%S"),
            "execution_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "env": "dev",
            "results": results,
            "type": "ai_collection",
            "scheduled": True
        }
        
        # 결과 파일 저장
        os.makedirs("results", exist_ok=True)
        result_file = os.path.join("results", f"test_result_{result_data['id']}.json")
        with open(result_file, "w", encoding="utf-8") as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)
            
        # 실패한 테스트 케이스에 대해 이슈 파일 생성
        for result in results:
            if result["result"] == "FAIL":
                issue_file = create_issue_file(result)
                print(f"이슈 파일 생성됨: {issue_file}")
            
        print(f"스케줄된 테스트가 완료되었습니다. 결과 파일: {result_file}")
        
    except Exception as e:
        print(f"스케줄된 테스트 실행 중 오류 발생: {str(e)}")

# 스케줄러에 작업 추가 (매주 토요일 14시에 실행)
scheduler.add_job(
    run_scheduled_test,
    trigger=CronTrigger(day_of_week='sat', hour=14, minute=0),
    id='weekly_test',
    replace_existing=True
)

# 사이드바에 메뉴 추가
st.sidebar.title("메뉴")
menu = st.sidebar.radio(
    "선택하세요",
    ["테스트 케이스 생성", "테스트 실행", "결과 확인", "테스트 케이스 관리", "대시보드", "결과 분석", "설정"]
)

# 테스트 케이스 생성기 인스턴스 생성
test_case_generator = TestCaseGenerator()

def convert_report_to_pdf(content):
    """마크다운 보고서를 PDF로 변환합니다."""
    try:
        # 마크다운을 HTML로 변환
        html_content = markdown2.markdown(content, extras=['fenced-code-blocks'])
        
        # HTML 스타일 추가
        html = f"""
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 40px;
                    line-height: 1.6;
                }}
                h1 {{
                    color: #2c3e50;
                    border-bottom: 2px solid #2c3e50;
                    padding-bottom: 10px;
                }}
                h2 {{
                    color: #34495e;
                    margin-top: 30px;
                }}
                h3 {{
                    color: #7f8c8d;
                }}
                .success {{
                    color: #27ae60;
                }}
                .failure {{
                    color: #e74c3c;
                }}
                .warning {{
                    color: #f39c12;
                }}
                pre {{
                    background-color: #f8f9fa;
                    padding: 15px;
                    border-radius: 5px;
                    overflow-x: auto;
                }}
                code {{
                    font-family: Consolas, monospace;
                }}
            </style>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """
        
        # PDF 생성 옵션
        options = {
            'encoding': 'UTF-8',
            'page-size': 'A4',
            'margin-top': '20mm',
            'margin-right': '20mm',
            'margin-bottom': '20mm',
            'margin-left': '20mm',
            'no-outline': None
        }
        
        # PDF 생성
        pdf = pdfkit.from_string(html, False, options=options)
        return pdf
    except Exception as e:
        st.error(f"PDF 생성 중 오류 발생: {str(e)}")
        return None

def get_binary_file_downloader_html(bin_file: bytes, file_label: str) -> str:
    """바이너리 파일을 다운로드 가능한 링크로 변환합니다."""
    b64 = base64.b64encode(bin_file).decode()
    return f'<a href="data:application/pdf;base64,{b64}" download="{file_label}">📥 {file_label} 다운로드</a>'

if menu == "테스트 케이스 생성":
    st.title("🤖 AI 테스트 케이스 생성")
    
    # 자연어 입력
    natural_language = st.text_area(
        "테스트 케이스를 생성할 요청을 자연어로 입력하세요.",
        height=200,
        placeholder="예: 사용자가 로그인한 후 장바구니에 상품을 추가하고 결제하는 테스트 케이스를 생성해줘"
    )
    
    if st.button("테스트 케이스 생성"):
        if not natural_language:
            st.warning("테스트 케이스 생성을 위한 요청을 입력해주세요.")
        else:
            with st.spinner("테스트 케이스를 생성 중입니다..."):
                # 테스트 케이스 생성
                result = test_case_generator.generate_test_case(natural_language)
                
                if result["status"] == "success":
                    test_case = result["test_case"]
                    test_case_id = result["test_case_id"]
                    
                    # 생성된 테스트 케이스 표시
                    st.success("테스트 케이스가 생성되었습니다!")
                    
                    # 테스트 케이스 정보 표시
                    st.subheader("테스트 케이스 정보")
                    st.write(f"ID: {test_case['id']}")
                    st.write(f"제목: {test_case['title']}")
                    st.write(f"설명: {test_case['description']}")
                    
                    # 테스트 단계 표시
                    st.subheader("테스트 단계")
                    for step in test_case["steps"]:
                        st.write(f"단계 {step['step_id']}: {step['action']}")
                        st.write(f"기대 결과: {step['expected_result']}")
                        st.write("---")
                    
                    # 전제 조건 및 후행 조건 표시
                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader("전제 조건")
                        for condition in test_case["preconditions"]:
                            st.write(f"- {condition}")
                    with col2:
                        st.subheader("후행 조건")
                        for condition in test_case["postconditions"]:
                            st.write(f"- {condition}")
                    
                    # 태그 표시
                    st.subheader("태그")
                    st.write(", ".join(test_case["tags"]))
                    
                    # 테스트 케이스 파일 내용 표시
                    st.subheader("생성된 테스트 케이스 파일")
                    try:
                        # 파일 경로 구성
                        feature_folder = "기타"
                        title = test_case.get("title", "").lower()
                        if any(keyword in title for keyword in ["결제", "payment", "pay", "카드", "계좌"]):
                            feature_folder = "결제"
                        elif any(keyword in title for keyword in ["로그인", "login", "signin", "로그인", "인증"]):
                            feature_folder = "로그인"
                        elif any(keyword in title for keyword in ["주문", "order", "구매", "장바구니", "cart"]):
                            feature_folder = "주문"
                        elif any(keyword in title for keyword in ["회원가입", "signup", "register", "가입", "회원"]):
                            feature_folder = "회원가입"
                        
                        filepath = os.path.join("cases", feature_folder, f"{test_case_id}.json")
                        with open(filepath, "r", encoding="utf-8") as f:
                            file_content = f.read()
                            st.code(file_content, language="json")
                    except Exception as e:
                        st.error(f"파일을 읽는 중 오류가 발생했습니다: {str(e)}")
                else:
                    st.error(f"테스트 케이스 생성 중 오류가 발생했습니다: {result['error']}")

elif menu == "테스트 실행":
    st.title("▶️ 테스트 실행")
    
    # 테스트 환경 선택
    env = st.selectbox("테스트 환경", ["개발", "스테이징", "운영"])
    
    # 실행 유형 선택
    test_type = st.radio("실행 유형", ["AI Collection", "Postman Collection"])
    
    if test_type == "AI Collection":
        # 테스트 케이스 선택
        cases = load_all_cases()
        selected_cases = st.multiselect(
            "실행할 테스트 케이스 선택",
            options=[f"{case['id']} - {case['title']}" for case in cases]
        )
        
        # 스케줄링 옵션
        schedule_type = st.radio("실행 방식", ["즉시 실행", "예약 실행"])
        if schedule_type == "예약 실행":
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("시작 날짜", min_value=datetime.now().date())
            with col2:
                start_time = st.time_input("시작 시간")
            
            # 반복 옵션
            repeat_type = st.selectbox("반복 유형", ["한 번만", "매일", "매주", "매월"])
            
            if repeat_type != "한 번만":
                if repeat_type == "매주":
                    days = st.multiselect(
                        "실행 요일",
                        ["월", "화", "수", "목", "금", "토", "일"],
                        default=["토"]
                    )
                elif repeat_type == "매월":
                    day_of_month = st.number_input("매월 몇 일", min_value=1, max_value=31, value=1)
            
            end_date = st.date_input("종료 날짜", min_value=start_date)
            
            # 스케줄 정보 표시
            st.info(f"예약된 테스트 실행 정보:\n"
                   f"- 시작: {start_date} {start_time}\n"
                   f"- 종료: {end_date}\n"
                   f"- 반복: {repeat_type}")
        
        # 실행 버튼
        if st.button("테스트 실행"):
            if not selected_cases:
                st.warning("실행할 테스트 케이스를 선택해주세요.")
            else:
                if schedule_type == "예약 실행":
                    # 스케줄링 설정
                    schedule_id = f"test_schedule_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    
                    # 반복 설정에 따른 트리거 생성
                    if repeat_type == "한 번만":
                        trigger = CronTrigger(
                            year=start_date.year,
                            month=start_date.month,
                            day=start_date.day,
                            hour=start_time.hour,
                            minute=start_time.minute
                        )
                    elif repeat_type == "매일":
                        trigger = CronTrigger(
                            hour=start_time.hour,
                            minute=start_time.minute
                        )
                    elif repeat_type == "매주":
                        trigger = CronTrigger(
                            day_of_week=','.join([str(i) for i in range(7) if ["월", "화", "수", "목", "금", "토", "일"][i] in days]),
                            hour=start_time.hour,
                            minute=start_time.minute
                        )
                    else:  # 매월
                        trigger = CronTrigger(
                            day=day_of_month,
                            hour=start_time.hour,
                            minute=start_time.minute
                        )
                    
                    # 스케줄러에 작업 추가
                    scheduler.add_job(
                        run_scheduled_test,
                        trigger=trigger,
                        id=schedule_id,
                        replace_existing=True,
                        end_date=end_date
                    )
                    
                    st.success(f"테스트가 예약되었습니다! (ID: {schedule_id})")
                else:
                    with st.spinner("테스트를 실행 중입니다..."):
                        results = run_selected_cases(selected_cases, env.lower())
                        
                        # 결과 처리
                        success_count = sum(1 for r in results if r["result"] == "PASS")
                        fail_count = sum(1 for r in results if r["result"] == "FAIL")
                        warning_count = sum(1 for r in results if r["result"] == "ERROR")
                        
                        # 결과 저장
                        result_data = {
                            "id": datetime.now().strftime("%Y%m%d%H%M%S"),
                            "execution_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "env": env,
                            "results": results,
                            "type": "ai_collection",
                            "scheduled": schedule_type == "예약 실행"
                        }
                        
                        # 결과 파일 저장
                        os.makedirs("results", exist_ok=True)
                        result_file = os.path.join("results", f"test_result_{result_data['id']}.json")
                        with open(result_file, "w", encoding="utf-8") as f:
                            json.dump(result_data, f, ensure_ascii=False, indent=2)
                        
                        # 세션 상태 업데이트
                        st.session_state.test_case_result = results
                        st.session_state.last_test_time = datetime.now()
                        st.session_state.test_type = "ai_collection"
                        
                        # 실패한 테스트 케이스에 대해 이슈 파일 생성
                        for result in results:
                            if result["result"] == "FAIL":
                                issue_file = create_issue_file(result)
                                print(f"이슈 파일 생성됨: {issue_file}")

        # 결과 표시
                        st.success("테스트가 완료되었습니다!")
                        st.metric("성공", success_count)
                        st.metric("실패", fail_count)
                        st.metric("경고", warning_count)
                        
                        # 상세 결과 표시
                        with st.expander("상세 결과 보기"):
                            for result in results:
                                # print(result)
                                st.subheader(f"테스트 케이스: {result['id']}")
                                st.write(f"상태: {result['result']}")
                                if result['result'] == 'FAIL':
                                    st.error(f"실패 사유: 상태 코드 {result.get('status_code', 'N/A')}")
                                elif result['result'] == 'ERROR':
                                    st.warning(f"경고 사유: {result['reason']}")
                                st.write("---")
    
    else:  # Postman Collection 실행
        st.subheader("Postman Collection 실행")
        collection_path = st.text_input("Postman Collection 경로", "postman/kakao_qa_collection.json")
        
        if st.button("Postman Collection 실행"):
            with st.spinner("Postman Collection을 실행 중입니다..."):
                result = run_postman_collection(collection_path)
                
                # 결과 저장
                result_data = {
                    "id": datetime.now().strftime("%Y%m%d%H%M%S"),
                    "execution_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "env": env,
                    "postman_result": result,
                    "type": "postman"
                }
                
                # 결과 파일 저장
                os.makedirs("results", exist_ok=True)
                result_file = os.path.join("results", f"test_result_{result_data['id']}.json")
                with open(result_file, "w", encoding="utf-8") as f:
                    json.dump(result_data, f, ensure_ascii=False, indent=2)
                
                # 세션 상태 업데이트
                st.session_state.postman_result = result
                st.session_state.last_test_time = datetime.now()
                st.session_state.test_type = "postman"
                
                if result["status"] == "success":
                    st.success("✅ Postman Collection 실행 완료!")
                    
                    # 결과 분석
                    output_lines = result["output"].split('\n')
                    success_count = sum(1 for line in output_lines if "✅" in line)
                    fail_count = sum(1 for line in output_lines if "❌" in line)
                    warning_count = sum(1 for line in output_lines if "⚠️" in line)
                    total_count = success_count + fail_count + warning_count
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("전체 실행", total_count)
                    with col2:
                        st.metric("성공률", f"{(success_count/total_count*100 if total_count > 0 else 0):.1f}%")
                    with col3:
                        st.metric("실패률", f"{(fail_count/total_count*100 if total_count > 0 else 0):.1f}%")
                    with col4:
                        st.metric("중단율", f"{(warning_count/total_count*100 if total_count > 0 else 0):.1f}%")
                    
                    # Postman 상세 결과
                    st.header("📝 Postman Collection 상세 결과")
                    with st.expander("상세 결과 보기"):
                        # 결과 요약 표시
                        st.markdown(f"### 📊 결과 요약")
                        st.markdown(f"- 총 요청 수: {total_count}")
                        st.markdown(f"- 성공: {success_count}")
                        st.markdown(f"- 실패: {fail_count}")
                        st.markdown(f"- 경고: {warning_count}")
                        st.markdown("---")
                        
                        # 상세 결과 표시
                        st.markdown("### 📝 상세 결과")
                        for line in output_lines:
                            if "✅" in line or "❌" in line or "⚠️" in line:
                                # 요청 정보 추출
                                request_info = line.split(" - ")
                                if len(request_info) > 1:
                                    method_name = request_info[0].strip()
                                    status = request_info[1].strip()
                                    
                                    # 요청 정보 표시
                                    st.markdown(f"#### {method_name}")
                                    if "✅" in status:
                                        st.success(f"상태: {status}")
                                    elif "❌" in status:
                                        st.error(f"상태: {status}")
                                    else:
                                        st.warning(f"상태: {status}")
                                    
                                    # URL 정보 표시
                                    for next_line in output_lines[output_lines.index(line)+1:]:
                                        if "URL:" in next_line:
                                            st.text(next_line)
                                            break
                                    
                                    # 응답 본문 또는 경고 메시지 표시
                                    if "❌" in status:
                                        for next_line in output_lines[output_lines.index(line)+1:]:
                                            if "응답 본문:" in next_line:
                                                st.code(next_line.replace("응답 본문:", "").strip(), language="json")
                                                break
                                    elif "⚠️" in status:
                                        for next_line in output_lines[output_lines.index(line)+1:]:
                                            if "실패 사유:" in next_line:
                                                st.text(next_line)
                                                break
                                else:
                                    st.text(line)
                            else:
                                st.text(line)  # 일반 텍스트 라인도 표시
                else:
                    st.error("❌ Postman Collection 실행 실패")
                    st.text(result["error"])

elif menu == "결과 확인":
    st.title("📊 테스트 결과 대시보드")
    
    # 테스트 유형에 따른 통계 표시
    if st.session_state.test_type == "postman" and st.session_state.postman_result:
        st.header("📈 Postman Collection 통계")
        result = st.session_state.postman_result
        if result["status"] == "success":
            # Postman 결과 분석
            output_lines = result["output"].split('\n')
            success_count = sum(1 for line in output_lines if "✅" in line)
            fail_count = sum(1 for line in output_lines if "❌" in line)
            warning_count = sum(1 for line in output_lines if "⚠️" in line)
            total_count = success_count + fail_count + warning_count
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("전체 실행", total_count)
            with col2:
                st.metric("성공률", f"{(success_count/total_count*100 if total_count > 0 else 0):.1f}%")
            with col3:
                st.metric("실패률", f"{(fail_count/total_count*100 if total_count > 0 else 0):.1f}%")
            with col4:
                st.metric("중단율", f"{(warning_count/total_count*100 if total_count > 0 else 0):.1f}%")
            
            # Postman 상세 결과
            st.header("📝 Postman Collection 상세 결과")
            with st.expander("상세 결과 보기"):
                # 결과 요약 표시
                st.markdown(f"### 📊 결과 요약")
                st.markdown(f"- 총 요청 수: {total_count}")
                st.markdown(f"- 성공: {success_count}")
                st.markdown(f"- 실패: {fail_count}")
                st.markdown(f"- 경고: {warning_count}")
                st.markdown("---")
                
                # 상세 결과 표시
                st.markdown("### 📝 상세 결과")
                for line in output_lines:
                    if "✅" in line or "❌" in line or "⚠️" in line:
                        # 요청 정보 추출
                        request_info = line.split(" - ")
                        if len(request_info) > 1:
                            method_name = request_info[0].strip()
                            status = request_info[1].strip()
                            
                            # 요청 정보 표시
                            st.markdown(f"#### {method_name}")
                            if "✅" in status:
                                st.success(f"상태: {status}")
                            elif "❌" in status:
                                st.error(f"상태: {status}")
                            else:
                                st.warning(f"상태: {status}")
                            
                            # URL 정보 표시
                            for next_line in output_lines[output_lines.index(line)+1:]:
                                if "URL:" in next_line:
                                    st.text(next_line)
                                    break
                            
                            # 응답 본문 또는 경고 메시지 표시
                            if "❌" in status:
                                for next_line in output_lines[output_lines.index(line)+1:]:
                                    if "응답 본문:" in next_line:
                                        st.code(next_line.replace("응답 본문:", "").strip(), language="json")
                                        break
                            elif "⚠️" in status:
                                for next_line in output_lines[output_lines.index(line)+1:]:
                                    if "실패 사유:" in next_line:
                                        st.text(next_line)
                                        break
                        else:
                            st.text(line)
                    else:
                        st.text(line)  # 일반 텍스트 라인도 표시
    
    elif st.session_state.test_type == "ai_collection" and st.session_state.test_case_result:
        st.header("📊 AI Collection 통계")
        results = st.session_state.test_case_result
        success_count = sum(1 for r in results if r["result"] == "PASS")
        fail_count = sum(1 for r in results if r["result"] == "FAIL")
        warning_count = sum(1 for r in results if r["result"] == "ERROR")
        total_count = len(results)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("전체 실행", total_count)
        with col2:
            st.metric("성공률", f"{(success_count/total_count*100 if total_count > 0 else 0):.1f}%")
        with col3:
            st.metric("실패률", f"{(fail_count/total_count*100 if total_count > 0 else 0):.1f}%")
        with col4:
            st.metric("중단율", f"{(warning_count/total_count*100 if total_count > 0 else 0):.1f}%")
        
        # AI Collection 상세 결과
        st.header("📝 AI Collection 상세 결과")
        with st.expander("상세 결과 보기"):
            for result in results:
                if result["result"] == "PASS":
                    st.success(f"✅ {result['id']} - {result['desc']}")
                elif result["result"] == "FAIL":
                    st.error(f"❌ {result['id']} - {result['desc']}")
                    st.code(result["body"], language="json")
                else:
                    st.warning(f"⚠️ {result['id']} - {result['desc']}")
                    st.text(result["reason"])
    
    else:
        st.info("실행된 테스트가 없습니다.")
    
    # 테스트 실행 선택 및 보고서 생성
    st.header("📋 보고서 생성")
    test_runs = load_test_runs()
    if test_runs:
        selected_run = st.selectbox("테스트 실행 선택", test_runs)
        
        # 보고서 생성
        if st.button("보고서 생성"):
            report = generate_test_report(selected_run)
            if report:
                # 보고서 내용 표시
                st.markdown(report)
                
                # PDF 생성 및 다운로드 버튼
                pdf_content = convert_report_to_pdf(report)
                if pdf_content:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    file_name = f"test_report_{timestamp}.pdf"
                    st.download_button(
                        "보고서 다운로드",
                        pdf_content,
                        file_name,
                        "application/pdf"
                    )
                else:
                    st.error("PDF 생성 중 오류가 발생했습니다.")
            else:
                st.error("보고서를 생성할 수 없습니다. 테스트 결과 파일이 올바른 형식인지 확인해주세요.")
    else:
        st.info("테스트 실행 이력이 없습니다.")

elif menu == "테스트 케이스 관리":
    st.title("📋 테스트 케이스 관리")
    
    # 검색 및 필터링 섹션
    st.header("🔍 테스트 케이스 검색")
    
    # 쿼리 파라미터를 사용한 필터 초기화 처리
    reset_filter = "reset_filter" in st.query_params
    
    # 검색 조건 입력
    col1, col2, col3 = st.columns(3)
    with col1:
        search_query = st.text_input("검색어 (제목, 설명, 태그)", value="" if reset_filter else None, key="search_query")
    with col2:
        search_type = st.selectbox("검색 유형", ["전체", "제목", "설명", "태그"], index=0 if reset_filter else None, key="search_type")
    with col3:
        feature_filter = st.selectbox(
            "기능",
            ["전체", "결제", "로그인", "주문", "회원가입", "기타"],
            index=0 if reset_filter else None,
            key="feature_filter"
        )
    
    # 초기화 후 쿼리 파라미터 제거
    if reset_filter:
        st.query_params.clear()
    
    # 필터 초기화 버튼
    if st.button("필터 초기화"):
        st.query_params["reset_filter"] = True
        st.rerun()
    
    # 모든 테스트 케이스 로드
    all_cases = load_all_cases()
    
    # 검색 결과 필터링
    filtered_cases = []
    for case in all_cases:
        should_include = True
        
        # 검색어 필터링
        if search_query:
            search_text = ""
            if search_type == "전체":
                search_text = f"{case.get('title', '')} {case.get('description', '')} {' '.join(case.get('tags', []))}"
            elif search_type == "제목":
                search_text = case.get('title', '')
            elif search_type == "설명":
                search_text = case.get('description', '')
            elif search_type == "태그":
                search_text = ' '.join(case.get('tags', []))
            
            if search_query.lower() not in search_text.lower():
                should_include = False
        
        # 기능 필터링
        if feature_filter != "전체":
            # 파일 경로에서 기능 추출
            filepath = case.get('filepath', '')
            case_feature = '기타'
            
            # 파일 경로 정규화
            filepath = filepath.replace('\\', '/') if '\\' in filepath else filepath
            
            # cases/기능디렉토리/파일명.json 형식에서 기능 디렉토리 추출
            path_parts = filepath.split('/')
            if len(path_parts) >= 2 and 'cases' in path_parts:
                cases_index = path_parts.index('cases')
                if len(path_parts) > cases_index + 1:
                    case_feature = path_parts[cases_index + 1]
            
            # 선택된 기능과 일치하지 않으면 제외
            if case_feature != feature_filter:
                should_include = False
        
        if should_include:
            filtered_cases.append(case)
    
    # 검색 결과 표시
    st.subheader(f"검색 결과 ({len(filtered_cases)}개)")
    
    if filtered_cases:
        # 결과를 그리드 형태로 표시
        for case in filtered_cases:
            with st.expander(f"📄 {case['title']}"):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**ID:** {case['id']}")
                    st.write(f"**설명:** {case['description']}")
                    st.write(f"**태그:** {', '.join(case.get('tags', []))}")
                    
                    # 파일 경로에서 기능 추출하여 표시
                    filepath = case.get('filepath', '')
                    case_feature = '기타'
                    
                    # 파일 경로 정규화
                    filepath = filepath.replace('\\', '/') if '\\' in filepath else filepath
                    
                    # cases/기능디렉토리/파일명.json 형식에서 기능 디렉토리 추출
                    path_parts = filepath.split('/')
                    if len(path_parts) >= 2 and 'cases' in path_parts:
                        cases_index = path_parts.index('cases')
                        if len(path_parts) > cases_index + 1:
                            case_feature = path_parts[cases_index + 1]
                        
                    st.write(f"**기능:** {case_feature}")
                    
                    st.write(f"**마지막 실행:** {case.get('last_execution', '미실행')}")
                    
                    # 테스트 케이스 수정 폼
                    with st.form(key=f"edit_form_{case['id']}"):
                        st.subheader("테스트 케이스 수정")
                        new_title = st.text_input("제목", value=case['title'])
                        new_description = st.text_area("설명", value=case['description'])
                        new_tags = st.text_input("태그 (쉼표로 구분)", value=','.join(case.get('tags', [])))
                        new_priority = st.selectbox("우선순위", ["높음", "중간", "낮음"], 
                                                  index=["높음", "중간", "낮음"].index(case.get('priority', '중간')))
                        
                        # 테스트 단계 수정
                        st.subheader("테스트 단계")
                        new_steps = []
                        for i, step in enumerate(case.get('steps', [])):
                            with st.container():
                                st.write(f"단계 {i+1}")
                                new_action = st.text_input(f"동작 {i+1}", value=step.get('action', ''), 
                                                        key=f"action_{case['id']}_{i}")
                                new_expected = st.text_input(f"기대 결과 {i+1}", value=step.get('expected_result', ''), 
                                                          key=f"expected_{case['id']}_{i}")
                                new_steps.append({
                                    'step_id': i+1,
                                    'action': new_action,
                                    'expected_result': new_expected
                                })
                        
                        # 전제 조건 및 후행 조건 수정
                        col1, col2 = st.columns(2)
                        with col1:
                            new_preconditions = st.text_area("전제 조건 (줄바꿈으로 구분)", 
                                                           value='\n'.join(case.get('preconditions', [])))
                        with col2:
                            new_postconditions = st.text_area("후행 조건 (줄바꿈으로 구분)", 
                                                            value='\n'.join(case.get('postconditions', [])))
                        
                        # 수정 버튼
                        if st.form_submit_button("수정"):
                            # 수정된 테스트 케이스 데이터 구성
                            updated_case = {
                                'id': case['id'],
                                'title': new_title,
                                'description': new_description,
                                'tags': [tag.strip() for tag in new_tags.split(',') if tag.strip()],
                                'priority': new_priority,
                                'steps': new_steps,
                                'preconditions': [cond.strip() for cond in new_preconditions.split('\n') if cond.strip()],
                                'postconditions': [cond.strip() for cond in new_postconditions.split('\n') if cond.strip()],
                                'filepath': case['filepath']
                            }
                            
                            # 파일 업데이트
                            try:
                                with open(case['filepath'], 'w', encoding='utf-8') as f:
                                    json.dump(updated_case, f, ensure_ascii=False, indent=2)
                                st.success("테스트 케이스가 성공적으로 수정되었습니다!")
                            except Exception as e:
                                st.error(f"테스트 케이스 수정 중 오류가 발생했습니다: {str(e)}")
                
                # 실행 버튼을 완전히 별도의 컨테이너로 이동
                st.write("")  # 빈 줄 추가
                if st.button("실행", key=f"run_{case['id']}_{hash(case['title'])}"):
                    run_test_case(case)
    else:
        st.info("검색 조건에 맞는 테스트 케이스가 없습니다.")

elif menu == "대시보드":
    st.title("📊 테스트 대시보드")
    
    # 테스트 실행 추이 그래프
    st.header("📈 테스트 실행 추이")
    test_history = load_test_history()
    fig = plot_test_trend(test_history)
    st.plotly_chart(fig)
    
    # 테스트 커버리지
    st.header("🎯 테스트 커버리지")
    coverage_data = calculate_coverage()
    st.altair_chart(plot_coverage(coverage_data))
    
    # 실패 패턴 분석
    st.header("🔍 실패 패턴 분석")
    failure_patterns = analyze_failure_patterns()
    st.dataframe(failure_patterns)

elif menu == "결과 분석":
    st.title("📊 결과 분석")
    
    # 테스트 실행 선택
    test_runs = load_test_runs()
    if not test_runs:
        st.warning("분석할 테스트 실행 이력이 없습니다.")
    else:
        selected_run = st.selectbox("분석할 테스트 실행 선택", test_runs)
        
        # 결과 비교
        st.header("🔄 결과 비교")
        compare_with = st.radio("비교 방식", ["단일 보고서", "비교 보고서"])
        
        if compare_with == "비교 보고서":
            comparison_type = st.selectbox("비교 대상 선택", ["이전 실행", "특정 실행"])
            
            comparison_run = None
            if comparison_type == "이전 실행":
                # 현재 선택된 실행의 바로 이전 실행을 자동으로 선택
                current_index = test_runs.index(selected_run)
                if current_index < len(test_runs) - 1:
                    comparison_run = test_runs[current_index + 1]
                    st.info(f"비교 대상: {comparison_run}")
                else:
                    st.warning("이전 실행이 없습니다.")
            else:  # "특정 실행"
                other_runs = [run for run in test_runs if run != selected_run]
                if other_runs:
                    comparison_run = st.selectbox("비교할 실행 선택", other_runs)
                else:
                    st.warning("비교할 다른 실행이 없습니다.")
            
            # 보고서 생성
            if st.button("보고서 생성"):
                if comparison_run:
                    report = generate_comparison_report(selected_run, comparison_run)
                    if report:
                        # 보고서 내용 표시
                        st.markdown(report)
                        
                        # 비교 불가능 메시지가 있는지 확인
                        if not report.startswith("# ⚠️ 테스트 결과 비교 불가"):
                            # PDF 생성 및 다운로드 버튼
                            pdf_content = convert_report_to_pdf(report)
                            if pdf_content:
                                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                file_name = f"test_comparison_report_{timestamp}.pdf"
                                st.download_button(
                                    "비교 보고서 다운로드",
                                    pdf_content,
                                    file_name,
                                    "application/pdf"
                                )
                            else:
                                st.error("PDF 생성 중 오류가 발생했습니다.")
                    else:
                        st.error("비교 보고서를 생성할 수 없습니다. 테스트 결과 파일이 올바른 형식인지 확인해주세요.")
                else:
                    st.error("비교할 실행을 선택해주세요.")
        else:  # "단일 보고서"
            # 기존 단일 보고서 생성
            if st.button("보고서 생성"):
                report = generate_test_report(selected_run)
                if report:
                    # 보고서 내용 표시
                    st.markdown(report)
                    
                    # PDF 생성 및 다운로드 버튼
                    pdf_content = convert_report_to_pdf(report)
                    if pdf_content:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        file_name = f"test_report_{timestamp}.pdf"
                        st.download_button(
                            "보고서 다운로드",
                            pdf_content,
                            file_name,
                            "application/pdf"
                        )
                    else:
                        st.error("PDF 생성 중 오류가 발생했습니다.")
                else:
                    st.error("보고서를 생성할 수 없습니다. 테스트 결과 파일이 올바른 형식인지 확인해주세요.")

elif menu == "설정":
    st.title("⚙️ 설정")
    
    # 설정 저장 함수
    def save_settings(settings):
        try:
            with open('.env', 'r', encoding='utf-8') as file:
                lines = file.readlines()
            
            updated_lines = []
            settings_added = {key: False for key in settings.keys()}
            
            for line in lines:
                key_added = False
                for setting_key, setting_value in settings.items():
                    if line.startswith(f"{setting_key}="):
                        updated_lines.append(f"{setting_key}={setting_value}\n")
                        settings_added[setting_key] = True
                        key_added = True
                        break
                if not key_added:
                    updated_lines.append(line)
            
            # 추가되지 않은 설정 추가
            for setting_key, added in settings_added.items():
                if not added:
                    updated_lines.append(f"{setting_key}={settings[setting_key]}\n")
            
            with open('.env', 'w', encoding='utf-8') as file:
                file.writelines(updated_lines)
        except Exception as e:
            st.error(f"설정 저장 중 오류가 발생했습니다: {str(e)}")
            raise e
    
    # JIRA 연동
    st.header("🔄 JIRA 연동 설정")
    
    # 현재 설정 로드
    with st.expander("JIRA 연동이란?", expanded=False):
        st.markdown("""
        **JIRA 연동을 통해 테스트 실패 시 자동으로 JIRA 이슈를 생성할 수 있습니다.**
        
        필요한 정보:
        1. **Jira 도메인**: Jira 인스턴스의 URL (예: https://your-domain.atlassian.net)
        2. **이메일**: Jira 계정 이메일
        3. **API 토큰**: Jira API 토큰 (Atlassian 계정 설정에서 생성 가능)
        4. **프로젝트 키**: 이슈를 생성할 Jira 프로젝트의 키 (예: QA, DEV)
        
        API 토큰 생성 방법:
        1. [Atlassian 계정 관리](https://id.atlassian.com/manage-profile/security/api-tokens)에 접속
        2. "Create API token" 클릭
        3. 토큰 이름 입력 후 생성
        4. 생성된 토큰을 안전한 곳에 보관
        """)
    
    # 입력 폼
    with st.form("jira_settings_form"):
        jira_domain = st.text_input("JIRA 도메인 (URL)", value=os.getenv('JIRA_DOMAIN', ''), placeholder="https://your-domain.atlassian.net")
        jira_email = st.text_input("JIRA 이메일", value=os.getenv('JIRA_EMAIL', ''), placeholder="your-email@example.com")
        jira_api_token = st.text_input("JIRA API 토큰", value=os.getenv('JIRA_API_TOKEN', ''), type="password", placeholder="API 토큰을 입력하세요")
        jira_project_key = st.text_input("JIRA 프로젝트 키", value=os.getenv('JIRA_PROJECT_KEY', ''), placeholder="예: QA, DEV")
        create_jira_issue = st.checkbox("테스트 실패 시 자동으로 JIRA 이슈 생성", value=os.getenv('CREATE_JIRA_ISSUE', 'false').lower() == 'true')
        
        col1, col2 = st.columns([1, 4])
        with col1:
            submit_button = st.form_submit_button("설정 저장")
        
        if submit_button:
            try:
                # 설정 저장
                settings = {
                    'JIRA_DOMAIN': jira_domain,
                    'JIRA_EMAIL': jira_email,
                    'JIRA_API_TOKEN': jira_api_token,
                    'JIRA_PROJECT_KEY': jira_project_key,
                    'CREATE_JIRA_ISSUE': 'true' if create_jira_issue else 'false'
                }
                save_settings(settings)
                st.success("JIRA 설정이 저장되었습니다!")
            except Exception as e:
                st.error(f"설정 저장 중 오류가 발생했습니다: {str(e)}")
    
    # 연결 테스트
    if st.button("JIRA 연결 테스트"):
        try:
            with st.spinner("JIRA 연결 테스트 중..."):
                jira_client = JiraAPI()
                result = jira_client.test_connection()
                
                if result['success']:
                    st.success(f"JIRA 연결 성공! 상태 코드: {result['status_code']}")
                    
                    # 프로젝트 정보 가져오기
                    if jira_project_key:
                        project_info = jira_client.get_project_info(jira_project_key)
                        if project_info['success']:
                            project_data = project_info['project_info']
                            st.write(f"프로젝트 정보:")
                            st.json({
                                'key': project_data.get('key'),
                                'name': project_data.get('name'),
                                'lead': project_data.get('lead', {}).get('displayName')
                            })
                        else:
                            st.warning(f"프로젝트 정보를 가져올 수 없습니다: {project_info.get('message')}")
                else:
                    st.error(f"JIRA 연결 실패: {result['message']}")
        except Exception as e:
            st.error(f"JIRA 연결 테스트 중 오류가 발생했습니다: {str(e)}")
    
    # 이슈 템플릿 설정
    with st.expander("이슈 템플릿 설정", expanded=False):
        st.markdown("JIRA 이슈 생성 시 사용될 템플릿을 설정합니다.")
        issue_template_title = st.text_area("이슈 제목 템플릿", 
                                            value=os.getenv('JIRA_ISSUE_TITLE_TEMPLATE', '[자동 생성] 테스트 실패: {test_id} - {description}'),
                                            help="사용 가능한 변수: {test_id}, {description}")
        
        issue_template_desc = st.text_area("이슈 설명 템플릿", 
                                          value=os.getenv('JIRA_ISSUE_DESC_TEMPLATE', """
테스트 ID: {test_id}
설명: {description}

## 오류 내용
{error}

## 요청/응답 데이터
```
{body}
```
                                          """),
                                          height=250,
                                          help="사용 가능한 변수: {test_id}, {description}, {error}, {body}")
        
        if st.button("템플릿 저장"):
            try:
                # 설정 저장
                settings = {
                    'JIRA_ISSUE_TITLE_TEMPLATE': issue_template_title,
                    'JIRA_ISSUE_DESC_TEMPLATE': issue_template_desc
                }
                save_settings(settings)
                st.success("이슈 템플릿이 저장되었습니다!")
            except Exception as e:
                st.error(f"템플릿 저장 중 오류가 발생했습니다: {str(e)}")
    
    st.divider()
    
    # Slack 연동
    st.header("📢 Slack 연동")
    slack_webhook = st.text_input("Slack Webhook URL", value=os.getenv('SLACK_WEBHOOK_URL', ''))
    
    notify_on_failure = st.checkbox("테스트 실패 시 알림", value=os.getenv('NOTIFY_ON_FAILURE', 'false').lower() == 'true')
    notify_on_completion = st.checkbox("테스트 완료 시 알림", value=os.getenv('NOTIFY_ON_COMPLETION', 'false').lower() == 'true')
    
    if st.button("Slack 설정 저장"):
        try:
            # 설정 저장
            settings = {
                'SLACK_WEBHOOK_URL': slack_webhook,
                'NOTIFY_ON_FAILURE': 'true' if notify_on_failure else 'false',
                'NOTIFY_ON_COMPLETION': 'true' if notify_on_completion else 'false'
            }
            save_settings(settings)
            st.success("Slack 설정이 저장되었습니다!")
        except Exception as e:
            st.error(f"설정 저장 중 오류가 발생했습니다: {str(e)}")
    
    # 환경 설정
    st.header("🌐 환경 설정")
    with st.expander("테스트 환경 설정"):
        st.markdown("테스트 실행에 사용될 환경 변수를 설정합니다.")
        
        env_settings = {}
        env_dev = st.text_input("개발 환경 URL", value=os.getenv('ENV_DEV', 'http://localhost:5000'), key="env_dev")
        env_stage = st.text_input("스테이징 환경 URL", value=os.getenv('ENV_STAGE', ''), key="env_stage")
        env_prod = st.text_input("운영 환경 URL", value=os.getenv('ENV_PROD', ''), key="env_prod")
        
        if st.button("환경 설정 저장"):
            try:
                # 설정 저장
                settings = {
                    'ENV_DEV': env_dev,
                    'ENV_STAGE': env_stage,
                    'ENV_PROD': env_prod
                }
                save_settings(settings)
                st.success("환경 설정이 저장되었습니다!")
            except Exception as e:
                st.error(f"설정 저장 중 오류가 발생했습니다: {str(e)}")
