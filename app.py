import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# ------------------------------------------------------
# 1. 설정 및 구글 시트 연결
# ------------------------------------------------------
st.set_page_config(page_title="[25-2] IHCO 시설관리실", page_icon="📅")

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error("설정 파일(secrets.toml) 오류입니다. 형식을 다시 확인해주세요.")
    st.stop()

def load_data(sheet_name):
    try:
        df = conn.read(worksheet=sheet_name, ttl=0)
        df = df.fillna("")
        df = df.astype(str)
        return df
    except Exception as e:
        return pd.DataFrame()

def save_to_gsheet(sheet_name, new_row_df):
    try:
        df = conn.read(worksheet=sheet_name, ttl=0)
        updated_df = pd.concat([df, new_row_df], ignore_index=True)
        conn.update(worksheet=sheet_name, data=updated_df)
        return True
    except Exception as e:
        st.error(f"저장 실패: {e}")
        return False

# ------------------------------------------------------
# 2. 관리자 설정
# ------------------------------------------------------
with st.sidebar:
    st.header("🔒 관리자 메뉴")
    admin_pw = st.text_input("비밀번호", type="password")
    
    # secrets에 설정이 없으면 1234로 동작
    if "admin_password" in st.secrets:
        correct_pw = st.secrets["admin_password"]
    else:
        correct_pw = "1234"

    is_admin = (admin_pw == correct_pw)
    if is_admin:
        st.success("관리자 로그인됨")

# ------------------------------------------------------
# 3. 화면 구성
# ------------------------------------------------------
st.title("📅 IHCO 시설관리실")

if is_admin:
    tab1, tab2, tab3, tab4 = st.tabs(["🔍 통합 조회", "➕ 봉사 등록", "🚨 무단결석 등록", "🚫 활동종료 관리"])
else:
    tab1, tab2 = st.tabs(["🔍 통합 조회", "🔒 관리자 전용"])
    with tab2:
        st.info("관리자만 접근 가능합니다.")

# [탭1] 통합 조회
with tab1:
    st.write("### 활동 내역 조회")
    c1, c2 = st.columns(2)
    in_name = c1.text_input("이름", placeholder="예: 김이코")
    in_birth = c2.text_input("생년월일 (YYYY-MM-DD)", placeholder="예: 2000-01-01")
    
    if st.button("조회"):
        if in_name and in_birth:
            name_clean = in_name.strip()
            birth_clean = in_birth.strip()

            # 데이터 로드
            df_service = load_data("시트1")
            df_penalty = load_data("무단결석")
            df_end = load_data("활동종료")

            found_something = False

            # ====================================================
            # 🚨 0순위: 활동 종료 대상자 확인
            # ====================================================
            is_terminated = False
            if not df_end.empty and '이름' in df_end.columns and '생년월일' in df_end.columns:
                cond_end = (df_end['이름'] == name_clean) & (df_end['생년월일'] == birth_clean)
                result_end = df_end[cond_end]
                
                if not result_end.empty:
                    found_something = True
                    is_terminated = True
                    absent_dates_str = result_end.iloc[0]['무단결석일자']
                    
                    st.error(f"🚫 **{name_clean}** 님 활동 종료 안내")
                    st.markdown(f"""
                    **그동안 IHCO 시설관리실 봉사에 참여해주셔서 감사드립니다.**
                    
                    무단결석 3회이상 누적으로 활동이 종료되었습니다.
                    
                    ---
                    * **무단결석 일자:** {absent_dates_str}
                    * **조치 사항:** 즉시 활동 종료 및 **다음 기수 선발 제한**
                    ---
                    """)
                    st.divider()

            # ====================================================
            # 1. 봉사 내역 확인
            # ====================================================
            if not df_service.empty and '봉사자 이름' in df_service.columns and '생년월일' in df_service.columns:
                cond = (df_service['봉사자 이름'] == name_clean) & (df_service['생년월일'] == birth_clean)
                result = df_service[cond]
                
                if not result.empty:
                    found_something = True
                    count = len(result)
                    dates = sorted(result['일시'].unique())
                    
                    if is_terminated:
                        st.warning(f"📄 **기존 활동 내역 (참고용)**: 총 {count}회")
                    else:
                        st.success(f"✅ **{name_clean}** 님의 봉사 내역입니다.")
                        st.metric("총 봉사 횟수", f"{count}회")
                    
                    with st.expander("봉사 참여 날짜 보기"):
                        st.table(dates)
            
            # ====================================================
            # 2. 무단결석 내역 확인
            # ====================================================
            if not df_penalty.empty and '이름' in df_penalty.columns and '생년월일' in df_penalty.columns:
                cond_p = (df_penalty['이름'] == name_clean) & (df_penalty['생년월일'] == birth_clean)
                result_p = df_penalty[cond_p]
                
                if not result_p.empty:
                    found_something = True
                    if not is_terminated:
                        st.divider()
                        st.error(f"🚨 현재 무단결석 내역이 **{len(result_p)}건** 있습니다.")
                        
                        for index, row in result_p.iterrows():
                            absent_date = row['일시']
                            penalty_date = row['패널티 일자']
                            penalty_count = row['무단결석 횟수'] if '무단결석 횟수' in row else ""

                            st.warning(f"""
                            * **무단결석 횟수:** {penalty_count}회
                            * **무단결석 일자:** {absent_date}
                            * **패널티 일자:** {penalty_date}
                            """)

                        # ----------------------------------------------------
                        # 문구 원상복구 (질문자님이 주신 텍스트 그대로)
                        # 모바일 줄바꿈을 위해 목록 기호(*)와 언더바(_)만 사용
                        # ----------------------------------------------------
                        with st.expander("🚨 무단결석 및 패널티 규정", expanded=False):
                            st.markdown("""
                            **무단결석 1회당 → 패널티 봉사 2회 진행**

                            1) 패널티 봉사 2회차 봉사시간만 지급
                            2) 패널티 봉사 1회 결석시, 출석 1회 봉사시간 미지급
                            3) 패널티 봉사 2회 결석시, 무단결석 횟수 추가
                            
                            ** 패널티 봉사는 익월 봉사가 원칙
                            ** 패널티 봉사 횟수는 수상 기준에 미포함 **
                            ** 패널티 봉사 미이행에 따른 2차 패널티 봉사는 없음.

                            ---
                            
                            _ex. 10월 1일 -> 패널티 봉사 11월 1일, 11월 2일 진행_
                            
                            * _11월 1일, 2일 모두 진행 O -> 11월 2일 봉사시간만 지급_
                            * _11월 1일 미진행, 2일 진행 -> 11월 2일 봉사시간 미지급_
                            * _11월 1일 미진행, 2일 미진행 -> 무단결석 횟수 1회 추가_

                            + 패널티 봉사는 상장 기준에 미포함됩니다
                            """)

            # ====================================================
            # 3. 결과 없음 / 일반 안내문구
            # ====================================================
            if found_something:
                if not is_terminated:
                    st.divider()
                    st.info("""
                    **봉사에 성실히 참여해주셔서 감사드립니다! 💖**
                    
                    **[상장 기준 안내]** 👀
                    * 감사장/공로상은 '원래 소속된 본부의 수료기준'을 충족 시 발급됩니다.
                    * 2월 활동 종료 시점까지 활동 종료 패널티 및 중도 이탈이 없어야 발급됩니다.
                    * 표창기준은 6개월동안, 6회 참여시, 감사장 / 8회 참여시, 공로상이 발급됩니다.
                    * 패널티 봉사 제외 일반 봉사 기준으로 횟수가 산정되니, 참고 부탁드립니다. ❗
                    * 상장은 활동 종료 후, 1~2주일 이내에 조직관리실 일괄 발급됩니다.
                    """)
                    st.caption("💡 혹시 봉사에 참여했는데도 횟수가 정상적으로 뜨지 않으면, **오픈채팅방**으로 연락주세요.")
            else:
                st.warning(f"'{name_clean}' 님의 조회된 내역이 없습니다.")
                st.write(f"👉 **{name_clean}** 님은 아직 봉사에 참여하지 않으셨습니다.")
                st.write("혹시 봉사에 참여했는데도 횟수가 정상적으로 뜨지 않으면, **오픈채팅방**으로 연락주세요.")
        else:
            st.warning("이름과 생년월일을 모두 입력해주세요.")

# [탭2] 봉사 등록
if is_admin:
    with tab2:
        st.subheader("➕ 봉사 시간 등록")
        with st.form("save_service"):
            c1, c2 = st.columns(2)
            d_date = c1.date_input("날짜", datetime.today())
            d_name = c2.text_input("이름")
            d_birth = st.text_input("생년월일 (YYYY-MM-DD)")
            
            if st.form_submit_button("봉사 저장"):
                if d_name and d_birth:
                    new_row = pd.DataFrame([{
                        '일시': d_date.strftime("%Y-%m-%d"),
                        '봉사자 이름': d_name,
                        '생년월일': d_birth
                    }])
                    if save_to_gsheet("시트1", new_row):
                        st.success("저장 완료!")

    # [탭3] 무단결석 등록
    with tab3:
        st.subheader("🚨 무단결석 등록")
        with st.form("save_penalty"):
            c1, c2 = st.columns(2)
            p_date = c1.date_input("결석 날짜", datetime.today())
            p_name = c2.text_input("이름")
            
            c3, c4 = st.columns(2)
            p_birth = c3.text_input("생년월일 (YYYY-MM-DD)")
            p_penalty_date = c4.text_input("패널티 일자", placeholder="예: 11월 1일, 2일")
            
            p_count = st.text_input("무단결석 횟수", value="1", placeholder="숫자 입력")

            if st.form_submit_button("결석 저장"):
                if p_name and p_birth:
                    new_row = pd.DataFrame([{
                        '일시': p_date.strftime("%Y-%m-%d"),
                        '이름': p_name,
                        '생년월일': p_birth,
                        '패널티 일자': p_penalty_date,
                        '무단결석 횟수': p_count
                    }])
                    if save_to_gsheet("무단결석", new_row):
                        st.error("저장 완료.")

    # [탭4] 활동종료 등록
    with tab4:
        st.subheader("🚫 활동 종료자 등록")
        with st.form("save_termination"):
            c1, c2 = st.columns(2)
            t_name = c1.text_input("이름")
            t_birth = c2.text_input("생년월일 (YYYY-MM-DD)")
            t_dates = st.text_input("무단결석 일자들", placeholder="예: 09-01, 10-05, 11-11")
            
            if st.form_submit_button("종료 처리 저장"):
                if t_name and t_birth and t_dates:
                    new_row = pd.DataFrame([{
                        '이름': t_name,
                        '생년월일': t_birth,
                        '무단결석일자': t_dates
                    }])
                    if save_to_gsheet("활동종료", new_row):
                        st.error(f"{t_name}님 활동 종료 처리 완료.")
