import streamlit as st
import requests
import pandas as pd

# ======================================================
# PAGE CONFIG
# ======================================================

st.set_page_config(
    page_title="V Studio Fashion Intelligence",
    page_icon="📊",
    layout="wide"
)

# ======================================================
# SECRETS
# ======================================================

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

# ======================================================
# LOAD DATA
# ======================================================

@st.cache_data(ttl=60)
def load_trends():
    url = f"{SUPABASE_URL}/rest/v1/fashion_trend_score"

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }

    params = {
        "select": "*",
        "order": "combined_score.desc"
    }

    response = requests.get(
        url,
        headers=headers,
        params=params,
        timeout=20
    )

    response.raise_for_status()

    return response.json()


# ======================================================
# HEADER
# ======================================================

st.title("V Studio — Fashion Intelligence")

st.caption(
    "Google Trends · Pinterest Trends · TikTok"
)

# ======================================================
# DATA
# ======================================================

try:
    data = load_trends()

    if not data:
        st.warning("Nessun trend trovato nel database.")
        st.stop()

    df = pd.DataFrame(data)

    st.success(
        f"Connessione a Supabase riuscita — {len(df)} trend caricati."
    )

    # ==================================================
    # TOP TREND
    # ==================================================

    top = df.iloc[0]

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Top Trend",
            top.get("trend_name", "-")
        )

    with col2:
        st.metric(
            "Fashion Score",
            top.get("combined_score", "-")
        )

    with col3:
        st.metric(
            "Momentum",
            top.get("momentum_label", "-")
        )

    with col4:
        st.metric(
            "Action",
            top.get("action_label", "-")
        )

    st.divider()

    # ==================================================
    # TABLE
    # ==================================================

    st.subheader("Trend Intelligence")

    wanted_columns = [
        "trend_name",
        "fashion_category",
        "combined_score",
        "google_score",
        "pinterest_score",
        "tiktok_score",
        "momentum_label",
        "action_label",
        "source_summary"
    ]

    available_columns = [
        col
        for col in wanted_columns
        if col in df.columns
    ]

    st.dataframe(
        df[available_columns],
        use_container_width=True,
        hide_index=True
    )

except Exception as e:
    st.error("Errore nel collegamento a Supabase.")
    st.code(str(e))
