# ============================================
# 어제의 박스오피스 앱
# KOBIS(영화관입장권통합전산망) 일별 박스오피스 API 사용
# 초보자도 이해하기 쉽게 주석을 달았습니다.
# ============================================

import streamlit as st
import requests
import pandas as pd

# 한국 시간 계산을 위한 라이브러리
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


# --------------------------------------------
# 1. 페이지 기본 설정
# --------------------------------------------

st.set_page_config(
    page_title="어제의 박스오피스",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 어제의 박스오피스")
st.caption("KOBIS 공식 API를 이용해 한국 시간 기준 어제의 영화 순위를 보여줍니다.")


# --------------------------------------------
# 2. 한국 시간 기준으로 '어제' 날짜 계산
# --------------------------------------------

# 배포 서버가 해외에 있어도 한국 시간을 기준으로 계산합니다.
korea_time = datetime.now(ZoneInfo("Asia/Seoul"))

# 오늘 날짜에서 하루를 빼서 어제 날짜를 구합니다.
yesterday = korea_time - timedelta(days=1)

# KOBIS API가 요구하는 날짜 형식: YYYYMMDD
target_date = yesterday.strftime("%Y%m%d")

# 화면에 보여줄 날짜 형식
display_date = yesterday.strftime("%Y년 %m월 %d일")


# --------------------------------------------
# 3. KOBIS API를 호출하는 함수
# --------------------------------------------

# 같은 날짜의 결과를 1시간 동안 캐시합니다.
# 따라서 페이지를 새로고침해도 한 시간 동안은
# API를 다시 호출하지 않습니다.
@st.cache_data(ttl=3600)
def get_boxoffice(target_dt):
    """
    KOBIS 일별 박스오피스 API를 호출하는 함수입니다.
    target_dt: YYYYMMDD 형식의 날짜
    """

    # Streamlit Cloud의 Secrets에서 인증키를 가져옵니다.
    # 실제 인증키를 코드에 직접 적으면 안 됩니다.
    try:
        api_key = st.secrets["KOBIS_KEY"]
    except Exception:
        return {
            "success": False,
            "message": (
                "KOBIS_KEY를 찾을 수 없습니다.\n\n"
                "Streamlit Cloud의 앱 설정에서 Secrets를 확인하세요."
            ),
            "data": None
        }

    # KOBIS 공식 API 주소
    url = (
        "https://www.kobis.or.kr/kobisopenapi/"
        "webservice/rest/boxoffice/"
        "searchDailyBoxOfficeList.json"
    )

    # API에 보낼 요청값
    params = {
        "key": api_key,
        "targetDt": target_dt
    }

    try:
        # API 요청
        response = requests.get(
            url,
            params=params,
            timeout=10
        )

        # HTTP 오류가 발생했는지 확인합니다.
        response.raise_for_status()

        # JSON 형태의 응답을 가져옵니다.
        result = response.json()

    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "message": (
                "KOBIS API 요청에 실패했습니다.\n\n"
                "인터넷 연결이나 KOBIS API 주소, "
                "API 서버 상태를 확인해 주세요."
            ),
            "data": None
        }

    except ValueError:
        return {
            "success": False,
            "message": (
                "KOBIS API의 응답을 읽을 수 없습니다.\n\n"
                "API가 정상적인 JSON 데이터를 보내는지 확인해 주세요."
            ),
            "data": None
        }

    # ----------------------------------------
    # 4. 인증키 오류 확인
    # ----------------------------------------
    # KOBIS는 인증키가 틀려도 HTTP 상태코드가 200일 수 있습니다.
    # 대신 faultInfo가 응답에 들어옵니다.
    if "faultInfo" in result:
        fault_info = result["faultInfo"]

        # faultInfo 안의 메시지를 최대한 찾아서 보여줍니다.
        fault_message = (
            fault_info.get("message")
            or fault_info.get("faultstring")
            or "KOBIS API에서 오류를 반환했습니다."
        )

        return {
            "success": False,
            "message": (
                f"KOBIS API 오류가 발생했습니다.\n\n"
                f"오류 내용: {fault_message}\n\n"
                "Streamlit Secrets의 KOBIS_KEY가 정확한지 "
                "확인해 주세요."
            ),
            "data": None
        }

    # ----------------------------------------
    # 5. boxOfficeResult 확인
    # ----------------------------------------

    boxoffice = result.get("boxOfficeResult")

    if not boxoffice:
        return {
            "success": False,
            "message": (
                "박스오피스 결과를 찾을 수 없습니다.\n\n"
                "KOBIS API 응답 구조를 확인하거나 "
                "잠시 후 다시 시도해 주세요."
            ),
            "data": None
        }

    # 영화 목록 가져오기
    movie_list = boxoffice.get("dailyBoxOfficeList", [])

    # 영화 목록이 비어 있는 경우
    if not movie_list:
        return {
            "success": False,
            "message": (
                f"{display_date}의 영화 목록이 비어 있습니다.\n\n"
                "해당 날짜의 박스오피스 데이터가 아직 제공되지 않았거나 "
                "KOBIS API의 응답을 확인해야 합니다."
            ),
            "data": None
        }

    # 정상적으로 가져온 경우
    return {
        "success": True,
        "message": "",
        "data": movie_list
    }


# --------------------------------------------
# 6. API 호출
# --------------------------------------------

result = get_boxoffice(target_date)


# --------------------------------------------
# 7. 오류가 발생한 경우 안내
# --------------------------------------------

if not result["success"]:
    st.error("⚠️ 박스오피스 데이터를 가져오지 못했습니다.")

    # 여러 줄의 안내문을 화면에 표시합니다.
    st.warning(result["message"])

    st.info(
        """
        **확인할 사항**

        1. Streamlit Cloud의 Secrets에 `KOBIS_KEY`가 등록되어 있는지 확인
        2. 인증키를 복사할 때 앞뒤에 불필요한 공백이 없는지 확인
        3. KOBIS API 서버가 정상적으로 동작하는지 확인
        4. 인터넷 연결이 가능한지 확인
        5. 해당 날짜의 박스오피스 데이터가 존재하는지 확인
        """
    )

    # 오류가 발생했으므로 아래의 그래프와 표는 만들지 않습니다.
    st.stop()


# --------------------------------------------
# 8. 영화 데이터를 DataFrame으로 변환
# --------------------------------------------

movie_list = result["data"]

df = pd.DataFrame(movie_list)


# --------------------------------------------
# 9. 숫자로 변환
# --------------------------------------------
# KOBIS API는 숫자도 문자열로 보내므로
# 정렬과 그래프를 위해 숫자로 변환합니다.

numeric_columns = [
    "rank",
    "audiCnt",
    "audiAcc",
    "scrnCnt"
]

for column in numeric_columns:
    df[column] = pd.to_numeric(
        df[column],
        errors="coerce"
    )


# --------------------------------------------
# 10. 순위 기준으로 정렬
# --------------------------------------------

df = df.sort_values("rank").reset_index(drop=True)


# --------------------------------------------
# 11. 1위 영화 정보 가져오기
# --------------------------------------------

first_movie = df.iloc[0]

first_movie_name = first_movie["movieNm"]
first_audience = int(first_movie["audiCnt"])
first_total_audience = int(first_movie["audiAcc"])
first_screens = int(first_movie["scrnCnt"])


# --------------------------------------------
# 12. 조회 날짜 표시
# --------------------------------------------

st.subheader(f"📅 {display_date}")

st.write(
    f"한국 시간 기준으로 **어제({target_date})**의 "
    "일별 박스오피스입니다."
)


# --------------------------------------------
# 13. 1위 영화 크게 표시
# --------------------------------------------

st.header(f"🥇 1위: {first_movie_name}")

# 지표 카드 3개를 가로로 배치합니다.
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "어제 관객수",
        f"{first_audience:,}명"
    )

with col2:
    st.metric(
        "누적 관객수",
        f"{first_total_audience:,}명"
    )

with col3:
    st.metric(
        "스크린수",
        f"{first_screens:,}개"
    )


# --------------------------------------------
# 14. 관객수 상위 5편 막대그래프
# --------------------------------------------

st.header("📊 관객수 상위 5편")

# 관객수가 많은 순서로 정렬합니다.
top5 = (
    df.sort_values("audiCnt", ascending=False)
      .head(5)
      .copy()
)

# 영화명을 인덱스로 설정합니다.
chart_data = top5.set_index("movieNm")[["audiCnt"]]

# Streamlit의 기본 막대그래프를 사용합니다.
st.bar_chart(
    chart_data,
    x_label="영화",
    y_label="관객수"
)


# --------------------------------------------
# 15. 전체 박스오피스 표 만들기
# --------------------------------------------

st.header("🎥 전체 박스오피스")

# 화면에 보여줄 열만 선택합니다.
table_df = df[
    [
        "rank",
        "movieNm",
        "openDt",
        "audiCnt",
        "audiAcc",
        "scrnCnt"
    ]
].copy()


# 열 이름을 한국어로 변경합니다.
table_df = table_df.rename(
    columns={
        "rank": "순위",
        "movieNm": "영화명",
        "openDt": "개봉일",
        "audiCnt": "관객수",
        "audiAcc": "누적관객",
        "scrnCnt": "스크린수"
    }
)


# 숫자에 천 단위 쉼표가 보이도록 표시 형식을 지정합니다.
table_df["관객수"] = table_df["관객수"].map(
    lambda x: f"{int(x):,}" if pd.notna(x) else "-"
)

table_df["누적관객"] = table_df["누적관객"].map(
    lambda x: f"{int(x):,}" if pd.notna(x) else "-"
)

table_df["스크린수"] = table_df["스크린수"].map(
    lambda x: f"{int(x):,}" if pd.notna(x) else "-"
)


# 표 출력
st.dataframe(
    table_df,
    use_container_width=True,
    hide_index=True
)


# --------------------------------------------
# 16. 데이터 출처
# --------------------------------------------

st.caption(
    "데이터 출처: 영화관입장권통합전산망(KOBIS) 공식 일별 박스오피스 API"
)
