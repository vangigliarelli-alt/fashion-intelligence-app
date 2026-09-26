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
N8N_WEBHOOK_URL = st.secrets["N8N_WEBHOOK_URL"]

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
        "trend_name": "not.is.null",
        "combined_score": "not.is.null",
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
# TRIGGER N8N
# ======================================================

def trigger_n8n():

    response = requests.post(
        N8N_WEBHOOK_URL,
        json={
            "source": "streamlit_app",
            "action": "refresh_fashion_intelligence"
        },
        timeout=20
    )

    response.raise_for_status()

    return response

# ======================================================
# HEADER
# ======================================================

st.title("V Studio — Fashion Intelligence")

st.caption(
    "Google Trends · Pinterest Trends · TikTok"
)

# ======================================================
# ACTION BUTTONS
# ======================================================

button_col1, button_col2, button_col3 = st.columns(
    [1, 1, 4]
)

with button_col1:

    if st.button(
        "🔄 AGGIORNA ORA",
        type="primary",
        use_container_width=True
    ):

        try:

            with st.spinner(
                "Avvio aggiornamento Fashion Intelligence..."
            ):

                trigger_n8n()

            st.success(
                "Aggiornamento avviato correttamente."
            )

            st.info(
                "n8n sta elaborando Google, Pinterest e TikTok. "
                "Attendi qualche istante e poi premi RICARICA DATI."
            )

        except Exception as e:

            st.error(
                "Non sono riuscito ad avviare n8n."
            )

            st.code(str(e))

with button_col2:

    if st.button(
        "↻ RICARICA DATI",
        use_container_width=True
    ):

        st.cache_data.clear()
        st.rerun()

st.divider()

# ======================================================
# DATA
# ======================================================

try:

    data = load_trends()

    if not data:
        st.warning(
            "Nessun trend trovato nel database."
        )
        st.stop()

    df = pd.DataFrame(data)

    # ==================================================
    # BASIC CLEANUP
    # ==================================================

    df = df[
        df["trend_name"].notna()
        &
        df["combined_score"].notna()
    ].copy()

    df["combined_score"] = pd.to_numeric(
        df["combined_score"],
        errors="coerce"
    )

    df = df.dropna(
        subset=["combined_score"]
    )

    # ==================================================
    # CLEAN OLD / GENERIC SIGNALS
    # ==================================================

    blocked_terms = [
        "wallpaper",
        "fanart",
        "fan art",
        "iphone",
        "android",
        "phone case",
        "screen",
        "screensaver",
        "home decor",
        "porch decor",
        "decor",
        "nails",
        "nail",
        "makeup",
        "hairstyle",
        "caption",
        "captions",
        "meme",
        "gaming",
        "recipe",
        "food",
        "tattoo"
    ]

    generic_tiktok_terms = [
        "outfitinspo",
        "fashiontiktok",
        "fashiontok",
        "grwm",
        "ootd",
        "outfitideas",
        "outfitinspiration",
        "fitcheck",
        "fyp",
        "foryou",
        "foryoupage"
    ]

    def is_blocked(name):

        text = str(name).lower().strip()

        if any(
            term in text
            for term in blocked_terms
        ):
            return True

        if text in generic_tiktok_terms:
            return True

        return False

    df = df[
        ~df["trend_name"].apply(is_blocked)
    ].copy()

    # ==================================================
    # KEEP CURRENT ENGINE RECORDS
    # ==================================================

    if "fashion_category" in df.columns:

        current_mask = (
            df["fashion_category"].notna()
        )

        google_mask = (
            df["fashion_category"]
            .fillna("")
            .str.upper()
            .eq("GOOGLE MONITORED")
        )

        if "trend_level" in df.columns:

            tiktok_mask = (
                df["trend_level"].notna()
            )

        else:

            tiktok_mask = pd.Series(
                False,
                index=df.index
            )

        if "source_summary" in df.columns:

            pinterest_mask = (
                df["source_summary"]
                .fillna("")
                .str.lower()
                .str.contains("pinterest")
            )

        else:

            pinterest_mask = pd.Series(
                False,
                index=df.index
            )

        df = df[
            current_mask
            &
            (
                google_mask
                |
                tiktok_mask
                |
                pinterest_mask
            )
        ].copy()

    # ==================================================
    # REMOVE DUPLICATES
    # ==================================================

    df = df.sort_values(
        "combined_score",
        ascending=False
    )

    df = df.drop_duplicates(
        subset=["trend_name"],
        keep="first"
    )

    if df.empty:

        st.warning(
            "Nessun trend valido dopo la pulizia."
        )

        st.stop()

    # ==================================================
    # HELPERS
    # ==================================================

    def safe_first(frame):

        if frame.empty:
            return None

        return frame.iloc[0]

    # ==================================================
    # TOP GOOGLE
    # ==================================================

    google_df = df[
        df.get(
            "source_summary",
            pd.Series("", index=df.index)
        )
        .fillna("")
        .str.lower()
        .str.contains("google")
    ].sort_values(
        "combined_score",
        ascending=False
    )

    top_google = safe_first(
        google_df
    )

    # ==================================================
    # TOP MATERIAL
    # ==================================================

    materials_df = df[
        df.get(
            "fashion_category",
            pd.Series("", index=df.index)
        )
        .fillna("")
        .str.upper()
        .eq("MATERIALS")
    ].sort_values(
        "combined_score",
        ascending=False
    )

    top_material = safe_first(
        materials_df
    )

    # ==================================================
    # TOP COLOR
    # ==================================================

    colors_df = df[
        df.get(
            "fashion_category",
            pd.Series("", index=df.index)
        )
        .fillna("")
        .str.upper()
        .eq("COLORS")
    ].sort_values(
        "combined_score",
        ascending=False
    )

    top_color = safe_first(
        colors_df
    )

    # ==================================================
    # TOP EMERGING
    # ==================================================

    if "trend_level" in df.columns:

        emerging_df = df[
            df["trend_level"]
            .fillna("")
            .str.upper()
            .eq("EMERGING TREND")
        ].sort_values(
            "combined_score",
            ascending=False
        )

    else:

        emerging_df = pd.DataFrame()

    top_emerging = safe_first(
        emerging_df
    )

    # ==================================================
    # CROSS SOURCE
    # ==================================================

    if "source_count" in df.columns:

        cross_df = df[
            pd.to_numeric(
                df["source_count"],
                errors="coerce"
            ).fillna(0) >= 2
        ].sort_values(
            "combined_score",
            ascending=False
        )

    else:

        cross_df = pd.DataFrame()

    top_cross = safe_first(
        cross_df
    )

    # ==================================================
    # STATUS
    # ==================================================

    st.success(
        f"Fashion Intelligence attiva — "
        f"{len(df)} trend validi caricati."
    )

    # ==================================================
    # KPI CARDS
    # ==================================================

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:

        if top_google is not None:

            st.metric(
                "📈 Top Google Trend",
                str(
                    top_google.get(
                        "trend_name",
                        "-"
                    )
                )
            )

            st.caption(
                f"Score "
                f"{top_google.get('combined_score', '-')}"
            )

        else:

            st.metric(
                "📈 Top Google Trend",
                "-"
            )

    with col2:

        if top_material is not None:

            st.metric(
                "🧵 Top Material",
                str(
                    top_material.get(
                        "trend_name",
                        "-"
                    )
                )
            )

            st.caption(
                f"Score "
                f"{top_material.get('combined_score', '-')}"
            )

        else:

            st.metric(
                "🧵 Top Material",
                "-"
            )

    with col3:

        if top_color is not None:

            st.metric(
                "🎨 Top Color",
                str(
                    top_color.get(
                        "trend_name",
                        "-"
                    )
                )
            )

            st.caption(
                f"Score "
                f"{top_color.get('combined_score', '-')}"
            )

        else:

            st.metric(
                "🎨 Top Color",
                "-"
            )

    with col4:

        if top_emerging is not None:

            st.metric(
                "🚀 Emerging Signal",
                str(
                    top_emerging.get(
                        "trend_name",
                        "-"
                    )
                )
            )

            st.caption(
                f"Score "
                f"{top_emerging.get('combined_score', '-')}"
            )

        else:

            st.metric(
                "🚀 Emerging Signal",
                "-"
            )

    with col5:

        if top_cross is not None:

            st.metric(
                "🔗 Cross-Source",
                str(
                    top_cross.get(
                        "trend_name",
                        "-"
                    )
                )
            )

            st.caption(
                f"{top_cross.get('source_count', '-')} fonti"
            )

        else:

            st.metric(
                "🔗 Cross-Source",
                "-"
            )

            st.caption(
                "Nessuna conferma multipla"
            )

    st.divider()

    # ==================================================
    # TREND INTELLIGENCE
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

    # ==================================================
    # SOURCE FILTER
    # ==================================================

    if (
        source_choice != "Tutte"
        and
        "source_summary"
        in filtered_df.columns
    ):

        source_map = {
            "Google": "google",
            "Pinterest": "pinterest",
            "TikTok": "tiktok"
        }

        selected_source = (
            source_map[
                source_choice
            ]
        )

        filtered_df = filtered_df[
            filtered_df[
                "source_summary"
            ]
            .fillna("")
            .str.lower()
            .str.contains(
                selected_source
            )
        ].copy()

    # ==================================================
    # CATEGORY FILTER
    # ==================================================

    if (
        "fashion_category"
        in filtered_df.columns
    ):

        categories = sorted(
            [
                str(x)
                for x
                in filtered_df[
                    "fashion_category"
                ]
                .dropna()
                .unique()
            ]
        )

        category_choice = st.selectbox(
            "Categoria",
            ["Tutte"] + categories
        )

        if (
            category_choice
            != "Tutte"
        ):

            filtered_df = filtered_df[
                filtered_df[
                    "fashion_category"
                ]
                ==
                category_choice
            ].copy()

    # ==================================================
    # TREND LEVEL FILTER
    # ==================================================

    if (
        source_choice == "TikTok"
        and
        "trend_level"
        in filtered_df.columns
    ):

        level_choice = st.selectbox(
            "Trend Level",
            [
                "Tutti",
                "CONFIRMED TREND",
                "EMERGING TREND",
                "SINGLE VIDEO SIGNAL"
            ]
        )

        if (
            level_choice
            != "Tutti"
        ):

            filtered_df = filtered_df[
                filtered_df[
                    "trend_level"
                ]
                ==
                level_choice
            ].copy()

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
        "trend_level",
        "momentum_label",
        "action_label",
        "video_count",
        "author_count",
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
            "trend_level": "Trend Level",
            "momentum_label": "Momentum",
            "action_label": "Action",
            "video_count": "Video",
            "author_count": "Autori",
            "source_summary": "Fonte"
        }
    )

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        height=620
    )

except Exception as e:

    st.error(
        "Errore nel collegamento a Supabase."
    )

    st.code(str(e))
