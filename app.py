import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# ------------------------------------------------------
# 1. 설정 및 구글 시트 연결
# ------------------------------------------------------
st.set_page_config(page_title="IHCO 시설관리실 ", page_icon="📅")

# 연결 시도
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error("설정 파일(secrets.toml) 오류입니다. 형식을 다시 확인해주세요.")
    st.stop()

def load_data():
    try:
        # 데이터 읽기 (캐시 없이 즉시 로드)
        df = conn.read(ttl=0)
        # 문자열로 변환하여 에러 방지
        df = df.fillna("") # 빈칸 처리
        df = df.astype(str)
        return df
    except Exception as e:
        st.error(f"구글 시트 읽기 실패: {e}")
        return pd.DataFrame()

def save_to_gsheet(date, name, birth):
    try:
        # 기존 데이터 로드
        df = conn.read(ttl=0)
        
        # 새 데이터 생성
        new_row = pd.DataFrame([{
            '일시': date,
            '봉사자 이름': name,
            '생년월일': birth
        }])
        
        # 합치기
        updated_df = pd.concat([df, new_row], ignore_index=True)
        
        # 구글 시트에 업데이트
        conn.update(data=updated_df)
        return True
    except Exception as e:
        st.error(f"저장 실패: {e}")
        return False

# ------------------------------------------------------
# 2. 관리자 설정
# ------------------------------------------------------
with st.sidebar:
    st.header("🔒 관리자 메뉴")
    pw = st.text_input("비밀번호", type="password")
    is_admin = (pw == "1234") 
    if is_admin:
        st.success("관리자 로그인됨")

# ------------------------------------------------------
# 3. 화면 구성
# ------------------------------------------------------
st.title("📅 IHCO 시설관리실")

if is_admin:
    tab1, tab2 = st.tabs(["🔍 조회하기", "➕ 등록하기"])
else:
    tab1, tab2 = st.tabs(["🔍 조회하기", "🔒 관리자 전용"])

# [탭1] 조회
with tab1:
    st.write("### 봉사 횟수 확인")
    c1, c2 = st.columns(2)
    in_name = c1.text_input("이름", placeholder="예: 김이코")
    in_birth = c2.text_input("생년월일 (YYYY-MM-DD)", placeholder="예: 2000-01-01")
    
    if st.button("조회"):
        if in_name and in_birth:
            df = load_data()
            
            if not df.empty:
                # 공백 제거 및 비교
                name_clean = in_name.strip()
                birth_clean = in_birth.strip()
                
                # 시트 컬럼 이름이 정확해야 합니다! (일시, 봉사자 이름, 생년월일)
                if '봉사자 이름' in df.columns and '생년월일' in df.columns:
                    cond = (df['봉사자 이름'] == name_clean) & (df['생년월일'] == birth_clean)
                    result = df[cond]
                    
                    if not result.empty:
                        count = len(result)
                        dates = sorted(result['일시'].unique())
                        
                        st.success(f"✅ **{name_clean}** 님 확인되었습니다.")
                        st.metric("총 횟수", f"{count}회")
                        st.write("**참여 날짜**")
                        st.table(dates)
                    else:
                        st.error("일치하는 데이터가 없습니다.")
                else:
                    st.error("구글 시트의 첫 번째 줄(제목)을 확인해주세요. '일시', '봉사자 이름', '생년월일' 이어야 합니다.")
            else:
                st.warning("구글 시트가 비어있거나 연결되지 않았습니다.")

# [탭2] 등록
with tab2:
    if is_admin:
        st.subheader("📝 저장")
        with st.form("save"):
            c1, c2 = st.columns(2)
            d_date = c1.date_input("날짜", datetime.today())
            d_name = c2.text_input("이름")
            d_birth = st.text_input("생년월일 (YYYY-MM-DD)")
            
            if st.form_submit_button("저장"):
                if d_name and d_birth:
                    ret = save_to_gsheet(d_date.strftime("%Y-%m-%d"), d_name, d_birth)
                    if ret:
                        st.success("저장 완료!")
                        st.balloons()
    else:

        st.info("비밀번호를 입력하세요.")
