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

@st.cache_data(ttl=30)
def load_trends():

    url = f"{SUPABASE_URL}/rest/v1/fashion_trend_score"

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }

    params = {
        "select": "*",

        # escludiamo vecchi record incompleti
        "trend_name": "not.is.null",
        "combined_score": "not.is.null",
        "fashion_category": "not.is.null",
        "action_label": "not.is.null",

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
        st.warning(
            "Nessun trend valido trovato nel database."
        )
        st.stop()

    df = pd.DataFrame(data)

    # ==================================================
    # PULIZIA
    # ==================================================

    required_columns = [
        "trend_name",
        "combined_score",
        "fashion_category",
        "action_label"
    ]

    for col in required_columns:
        if col not in df.columns:
            st.error(
                f"Manca la colonna {col} nella tabella Supabase."
            )
            st.stop()

    df = df[
        df["trend_name"].notna() &
        df["combined_score"].notna() &
        df["fashion_category"].notna() &
        df["action_label"].notna()
    ].copy()

    df["combined_score"] = pd.to_numeric(
        df["combined_score"],
        errors="coerce"
    )

    df = df.dropna(
        subset=["combined_score"]
    )

    # ==================================================
    # RIMUOVIAMO EVENTUALI VECCHI RECORD SPORCHI
    # ==================================================

    bad_terms = [
        "wallpaper",
        "fanart",
        "fan art",
        "iphone",
        "nails",
        "nail",
        "porch decor",
        "home decor",
        "decor"
    ]

    mask_bad = df["trend_name"].str.lower().apply(
        lambda x: any(
            term in str(x)
            for term in bad_terms
        )
    )

    df = df[
        ~mask_bad
    ].copy()

    # ==================================================
    # ORDINA
    # ==================================================

    df = df.sort_values(
        "combined_score",
        ascending=False
    )

    st.success(
        f"Fashion Intelligence attiva — "
        f"{len(df)} trend validi caricati."
    )

    # ==================================================
    # TOP TREND
    # ==================================================

    top = df.iloc[0]

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Top Trend",
            str(
                top.get(
                    "trend_name",
                    "-"
                )
            )
        )

    with col2:
        st.metric(
            "Fashion Score",
            f"{float(top.get('combined_score', 0)):.1f}"
        )

    with col3:

        value = top.get(
            "momentum_label"
        )

        st.metric(
            "Momentum",
            "-" if pd.isna(value)
            else str(value)
        )

    with col4:

        value = top.get(
            "action_label"
        )

        st.metric(
            "Action",
            "-" if pd.isna(value)
            else str(value)
        )

    st.divider()

    # ==================================================
    # SOURCE FILTERS
    # ==================================================

    st.subheader(
        "Trend Intelligence"
    )

    source_choice = st.radio(
        "Fonte",
        [
            "Tutte",
            "Google",
            "Pinterest",
            "TikTok"
        ],
        horizontal=True
    )

    filtered_df = df.copy()

    if (
        source_choice != "Tutte" and
        "source_summary" in filtered_df.columns
    ):

        source_map = {
            "Google": "google",
            "Pinterest": "pinterest",
            "TikTok": "tiktok"
        }

        selected_source = source_map[
            source_choice
        ]

        filtered_df = filtered_df[
            filtered_df[
                "source_summary"
            ]
            .fillna("")
            .str.lower()
            .str.contains(
                selected_source
            )
        ]

    # ==================================================
    # TABLE
    # ==================================================

    wanted_columns = [
        "trend_name",
        "fashion_category",
        "combined_score",
        "google_score",
        "pinterest_score",
        "tiktok_score",
        "momentum_label",
        "action_label",
        "trend_level",
        "source_summary"
    ]

    available_columns = [
        col
        for col in wanted_columns
        if col in filtered_df.columns
    ]

    display_df = filtered_df[
        available_columns
    ].copy()

    display_df = display_df.rename(
        columns={
            "trend_name": "Trend",
            "fashion_category": "Categoria",
            "combined_score": "Fashion Score",
            "google_score": "Google",
            "pinterest_score": "Pinterest",
            "tiktok_score": "TikTok",
            "momentum_label": "Momentum",
            "action_label": "Action",
            "trend_level": "Trend Level",
            "source_summary": "Fonte"
        }
    )

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        height=600
    )

except Exception as e:

    st.error(
        "Errore nel collegamento a Supabase."
    )

    st.code(
        str(e)
    )
