import sys
import os
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
    generate_test_report
)
from test_engine.postman_runner import run_postman_collection
from test_engine.test_case_generator import TestCaseGenerator

# 페이지 설정
st.set_page_config(
    page_title="Kakao QA Lite",
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

# 사이드바에 메뉴 추가
st.sidebar.title("메뉴")
menu = st.sidebar.radio(
    "선택하세요",
    ["테스트 케이스 생성", "테스트 실행", "결과 확인", "테스트 케이스 관리", "대시보드", "결과 분석", "설정"]
)

# 테스트 케이스 생성기 인스턴스 생성
test_case_generator = TestCaseGenerator()

def convert_report_to_pdf(report_content: str) -> bytes:
    """마크다운 형식의 보고서를 PDF로 변환합니다."""
    try:
        # PDF 옵션 설정
        options = {
            'page-size': 'A4',
            'margin-top': '0.75in',
            'margin-right': '0.75in',
            'margin-bottom': '0.75in',
            'margin-left': '0.75in',
            'encoding': 'UTF-8',
            'enable-local-file-access': None
        }
        
        # 마크다운을 HTML로 변환
        html_content = markdown2.markdown(report_content)
        
        # HTML 스타일 추가
        styled_html = f"""
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; }}
                h1 {{ color: #2c3e50; }}
                h2 {{ color: #34495e; }}
                h3 {{ color: #7f8c8d; }}
                .success {{ color: #27ae60; }}
                .failure {{ color: #c0392b; }}
                .warning {{ color: #f39c12; }}
                pre {{ background-color: #f8f9fa; padding: 10px; border-radius: 5px; }}
                code {{ background-color: #f8f9fa; padding: 2px 4px; border-radius: 3px; }}
            </style>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """
        
        # HTML을 PDF로 변환
        pdf = pdfkit.from_string(styled_html, False, options=options)
        return pdf
    except Exception as e:
        st.error(f"PDF 생성 중 오류가 발생했습니다: {str(e)}")
        return None

def get_binary_file_downloader_html(bin_file: bytes, file_label: str) -> str:
    """바이너리 파일을 다운로드 가능한 링크로 변환합니다."""
    b64 = base64.b64encode(bin_file).decode()
    return f'<a href="data:application/pdf;base64,{b64}" download="{file_label}">📥 {file_label} 다운로드</a>'

if menu == "테스트 케이스 생성":
    st.title("🤖 AI 테스트 케이스 생성기")
    
    # 자연어 입력 받기
    user_input = st.text_area(
        "테스트 케이스를 생성하고 싶은 내용을 자연어로 입력하세요",
        placeholder="예: 회원가입 실패 케이스 만들어줘"
    )
    
    if st.button("테스트 케이스 생성"):
        if user_input:
            with st.spinner("테스트 케이스를 생성 중입니다..."):
                result = test_case_generator.generate_test_case(user_input)
                
                if result["status"] == "success":
                    st.success("테스트 케이스가 성공적으로 생성되었습니다!")
                    st.json(result["test_case"])
                    
                    # 생성된 테스트 케이스 파일 다운로드 버튼
                    with open(result["filepath"], "r", encoding="utf-8") as f:
                        st.download_button(
                            label="테스트 케이스 다운로드",
                            data=f,
                            file_name=os.path.basename(result["filepath"]),
                            mime="application/json"
                        )
                else:
                    st.error(f"테스트 케이스 생성 중 오류가 발생했습니다: {result['error']}")
        else:
            st.warning("테스트 케이스 생성을 위한 내용을 입력해주세요.")

elif menu == "테스트 실행":
    st.title("▶️ 테스트 실행")
    
    # 테스트 환경 선택
    env = st.selectbox("테스트 환경", ["개발", "스테이징", "운영"])
    
    # 실행 유형 선택
    test_type = st.radio("실행 유형", ["테스트 케이스", "Postman Collection"])
    
    if test_type == "테스트 케이스":
        # 테스트 케이스 선택
        cases = load_all_cases()
        selected_cases = st.multiselect(
            "실행할 테스트 케이스 선택",
            options=[f"{case['id']} - {case['title']}" for case in cases]
        )
        
        # 스케줄링 옵션
        schedule_type = st.radio("실행 방식", ["즉시 실행", "예약 실행"])
        if schedule_type == "예약 실행":
            scheduled_time = st.time_input("실행 시간")
        
        # 실행 버튼
        if st.button("테스트 실행"):
            if not selected_cases:
                st.warning("실행할 테스트 케이스를 선택해주세요.")
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
                        "type": "test_case"
                    }
                    
                    # 결과 파일 저장
                    os.makedirs("results", exist_ok=True)
                    result_file = os.path.join("results", f"test_result_{result_data['id']}.json")
                    with open(result_file, "w", encoding="utf-8") as f:
                        json.dump(result_data, f, ensure_ascii=False, indent=2)
                    
                    # 세션 상태 업데이트
                    st.session_state.test_case_result = results
                    st.session_state.last_test_time = datetime.now()
                    st.session_state.test_type = "test_case"
                    
                    # 결과 표시
                    st.success(f"테스트 실행 완료! (성공: {success_count}, 실패: {fail_count}, 오류: {warning_count})")
                    
                    # 상세 결과 표시
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
                    st.markdown("### 📊 실행 결과")
                    st.text(result["output"])
                else:
                    st.error("❌ Postman Collection 실행 실패")
                    st.text(result["error"])

elif menu == "결과 확인":
    st.title("📊 테스트 결과 대시보드")
    
    # Postman Collection 통계
    st.header("📈 Postman Collection 통계")
    if st.session_state.postman_result and st.session_state.test_type == "postman":
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
    
    # 테스트 케이스 통계
    st.header("📊 테스트 케이스 통계")
    if st.session_state.test_case_result and st.session_state.test_type == "test_case":
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
    
    # 최근 실행 결과
    st.header("🔄 최근 실행 결과")
    
    if st.session_state.last_test_time:
        st.info(f"마지막 실행: {st.session_state.last_test_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if st.session_state.test_type == "postman" and st.session_state.postman_result:
            result = st.session_state.postman_result
            if result["status"] == "success":
                st.success("✅ Postman Collection 실행 성공")
                st.markdown("### 📊 실행 결과")
                st.text(result["output"])
            else:
                st.error("❌ Postman Collection 실행 실패")
                st.text(result["error"])
        
        elif st.session_state.test_type == "test_case" and st.session_state.test_case_result:
            results = st.session_state.test_case_result
            for result in results:
                if result["result"] == "PASS":
                    st.success(f"✅ {result['id']} - {result['desc']}")
                elif result["result"] == "FAIL":
                    st.error(f"❌ {result['id']} - {result['desc']}")
                    st.code(result["body"], language="json")
                else:
                    st.warning(f"⚠️ {result['id']} - {result['desc']}")
                    st.text(result["reason"])

    # 테스트 실행 선택
    test_runs = load_test_runs()
    if test_runs:
        selected_run = st.selectbox("테스트 실행 선택", test_runs)
        compare_with = st.selectbox("비교할 실행 선택 (선택사항)", ["없음"] + test_runs)
        
        if st.button("보고서 생성"):
            compare = None if compare_with == "없음" else compare_with
            report_content = generate_test_report(selected_run, compare)
            
            if report_content:
                st.markdown(report_content)
                
                # PDF 생성 및 다운로드 버튼
                pdf_content = convert_report_to_pdf(report_content)
                if pdf_content:
                    st.markdown("### 📥 보고서 다운로드")
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    file_name = f"test_report_{timestamp}.pdf"
                    st.markdown(get_binary_file_downloader_html(pdf_content, file_name), unsafe_allow_html=True)
            else:
                st.error("보고서를 생성할 수 없습니다.")
    else:
        st.info("테스트 실행 이력이 없습니다.")

elif menu == "테스트 케이스 관리":
    st.title("📋 테스트 케이스 관리")
    
    # 테스트 케이스 검색 및 필터링
    search_query = st.text_input("테스트 케이스 검색")
    filter_tags = st.multiselect("태그 필터", ["회원가입", "로그인", "결제", "주문"])
    
    # 테스트 케이스 목록 표시
    cases = load_all_cases()
    filtered_cases = filter_cases(cases, search_query, filter_tags)
    
    # 테스트 케이스 그룹화
    grouped_cases = group_cases_by_feature(filtered_cases)
    
    for feature, feature_cases in grouped_cases.items():
        with st.expander(f"📁 {feature}"):
            for case in feature_cases:
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"**{case['title']}**")
                with col2:
                    st.selectbox("우선순위", ["높음", "중간", "낮음"], key=f"priority_{case['id']}")
                with col3:
                    if st.button("실행", key=f"run_{case['id']}"):
                        run_test_case(case)

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
    selected_run = st.selectbox("분석할 테스트 실행 선택", test_runs)
    
    # 결과 비교
    st.header("🔄 결과 비교")
    compare_with = st.selectbox("비교 대상 선택", ["이전 실행", "특정 실행"])
    if compare_with == "특정 실행":
        specific_run = st.selectbox("비교할 실행 선택", test_runs)
    
    # 보고서 생성
    if st.button("보고서 생성"):
        report = generate_test_report(selected_run, compare_with)
        st.download_button(
            "보고서 다운로드",
            report,
            "test_report.pdf",
            "application/pdf"
        )

elif menu == "설정":
    st.title("⚙️ 설정")
    
    # JIRA 연동
    st.header("JIRA 연동")
    jira_url = st.text_input("JIRA URL")
    jira_api_key = st.text_input("JIRA API Key", type="password")
    
    # Slack 연동
    st.header("Slack 연동")
    slack_webhook = st.text_input("Slack Webhook URL")
    
    # 알림 설정
    st.header("알림 설정")
    notify_on_failure = st.checkbox("테스트 실패 시 알림")
    notify_on_completion = st.checkbox("테스트 완료 시 알림")
 