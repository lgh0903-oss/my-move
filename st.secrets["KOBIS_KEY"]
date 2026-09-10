import streamlit as st
import requests
from datetime import date, timedelta

st.set_page_config(
    page_title="일별 박스오피스",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 일별 박스오피스")
st.write("원하는 날짜의 영화 순위를 확인해 보세요!")

# KOBIS API 인증키
try:
    KOBIS_KEY = st.secrets["KOBIS_KEY"]
except Exception:
    st.error("KOBIS_KEY가 Streamlit Secrets에 설정되어 있지 않습니다.")
    st.stop()

# 날짜 선택
yesterday = date.today() - timedelta(days=1)

selected_date = st.date_input(
    "📅 조회할 날짜를 선택하세요",
    value=yesterday,
    min_value=date(2000, 1, 1),
    max_value=yesterday
)

# 날짜를 YYYYMMDD 형식으로 변환
target_date = selected_date.strftime("%Y%m%d")

# KOBIS 일별 박스오피스 API
url = "https://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json"

params = {
    "key": KOBIS_KEY,
    "targetDt": target_date
}

try:
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()

except requests.RequestException:
    st.error("영화 정보를 가져오는 중 오류가 발생했습니다.")
    st.stop()

except ValueError:
    st.error("API에서 올바른 데이터를 받지 못했습니다.")
    st.stop()

# API 결과 확인
try:
    movies = data["boxOfficeResult"]["dailyBoxOfficeList"]
except (KeyError, TypeError):
    st.error("박스오피스 데이터를 확인할 수 없습니다.")
    st.stop()

# 영화 목록이 없는 경우
if not movies:
    st.warning("그날은 아직 집계 전입니다.")
    st.stop()

st.subheader(f"📊 {selected_date.strftime('%Y년 %m월 %d일')} 박스오피스")

# 표에 보여줄 데이터 만들기
table_data = []

for movie in movies:
    rank_inten = int(movie.get("rankInten", 0))
    audi_acc = int(movie.get("audiAcc", 0))

    # 순위 변동 표시
    if rank_inten > 0:
        rank_change = f"🔴⬆️ {rank_inten}"
    elif rank_inten < 0:
        rank_change = f"🔵⬇️ {abs(rank_inten)}"
    else:
        rank_change = "➖ 0"

    # 누적 관객 100만 명 초과/이상인 경우 트로피
    movie_name = movie.get("movieNm", "")

    if audi_acc > 1_000_000:
        movie_name += " 🏆"

    table_data.append({
        "순위": movie.get("rank", ""),
        "영화": movie_name,
        "순위 변동": rank_change,
        "일일 관객수": f"{int(movie.get('audiCnt', 0)):,}명",
        "누적 관객수": f"{audi_acc:,}명",
        "상영관 수": f"{int(movie.get('scrnCnt', 0)):,}개",
    })

st.dataframe(
    table_data,
    use_container_width=True,
    hide_index=True
)

st.caption("🔴⬆️ 순위 상승　🔵⬇️ 순위 하락　➖ 순위 변동 없음　🏆 누적 관객 100만 명 초과")
