import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# ------------------------------------------------------
# 1. 설정 및 구글 시트 연결
# ------------------------------------------------------
st.set_page_config(page_title="IHCO 시설관리실", page_icon="📅")

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error("설정 파일(secrets.toml) 오류입니다. 형식을 다시 확인해주세요.")
    st.stop()

def load_data():
    try:
        df = conn.read(ttl=0)
        df = df.fillna("") 
        df = df.astype(str)
        return df
    except Exception as e:
        st.error(f"구글 시트 읽기 실패: {e}")
        return pd.DataFrame()

def save_to_gsheet(date, name, birth):
    try:
        df = conn.read(ttl=0)
        new_row = pd.DataFrame([{
            '일시': date,
            '봉사자 이름': name,
            '생년월일': birth
        }])
        updated_df = pd.concat([df, new_row], ignore_index=True)
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
    admin_pw = st.text_input("비밀번호", type="password")
    
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
                name_clean = in_name.strip()
                birth_clean = in_birth.strip()
                
                if '봉사자 이름' in df.columns and '생년월일' in df.columns:
                    cond = (df['봉사자 이름'] == name_clean) & (df['생년월일'] == birth_clean)
                    result = df[cond]
                    
                    if not result.empty:
                        count = len(result)
                        dates = sorted(result['일시'].unique())
                        
                        st.success(f"✅ **{name_clean}** 님의 봉사 내역이 확인되었습니다!")
                        st.metric("총 횟수", f"{count}회")
                        st.write("**[참여 날짜]**")
                        st.table(dates)
                        
                        st.info("""
                        **봉사에 성실히 참여해주셔서 감사드립니다! 💖**
                        
                        **[상장 기준 안내]** 👀
                        * 감사장/공로상은 '원래 소속된 본부의 수료기준'을 충족 시 발급됩니다.
                        * 2월 활동 종료 시점까지 활동 종료 패널티 및 중도 이탈이 없어야 발급됩니다.
                        * 표창기준은 6개월 동안 **6회 참여시 감사장**, **8회 참여시 공로상**이 발급됩니다.
                        * 패널티 봉사 제외 일반 봉사 기준으로 횟수가 산정되니, 참고 부탁드립니다. ❗
                        * 상장은 활동 종료 후, 1~2주일 이내에 조직관리실 일괄 발급됩니다.
                        """)
                        
                        st.caption(f"💡 혹시 {count}회가 맞지 않다면, **오픈채팅방**으로 연락 주세요.")

                    else:
                        st.error(f"😢 **'{name_clean}'** 님은 아직 봉사에 참여하지 않으셨거나, 정보가 일치하지 않습니다.")
                        st.write("👉 참여하셨는데도 조회가 안 된다면, **오픈채팅방**으로 연락 주세요.")
                else:
                    st.error("구글 시트 제목 오류: '일시', '봉사자 이름', '생년월일' 확인 필요")
            else:
                st.warning("데이터가 없습니다.")

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
