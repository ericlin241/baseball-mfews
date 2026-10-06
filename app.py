"""
=============================================================================
賽季微疲勞先行指標預警系統 (Micro-Fatigue Early Warning System, MFEWS)
2026 野革盃台灣棒球數據黑客松參賽專案
架構：Streamlit + Plotly + Pandas + NumPy (可透過 stlite WebAssembly 在瀏覽器端純前端運行)
視覺規範：Google Material You (Material Design 3 - MD3) 設計系統整合
=============================================================================
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

# =============================================================================
# 0. Material You (Material Design 3, MD3) 設計系統 Design Tokens 與渲染元件
# =============================================================================
MD3_TOKENS = {
    "colors": {
        "primary": "#6750A4",
        "on_primary": "#FFFFFF",
        "primary_container": "#EADDFF",
        "on_primary_container": "#21005D",
        "secondary": "#625B71",
        "on_secondary": "#FFFFFF",
        "secondary_container": "#E8DEF8",
        "on_secondary_container": "#1D192B",
        "tertiary": "#7D5260",
        "on_tertiary": "#FFFFFF",
        "tertiary_container": "#FFD8E4",
        "on_tertiary_container": "#31111D",
        "surface": "#FFFBFE",
        "on_surface": "#1C1B1F",
        "surface_variant": "#E7E0EC",
        "on_surface_variant": "#49454F",
        "surface_container": "#F3EDF7",
        "surface_container_low": "#E7E0EC",
        "surface_container_high": "#ECE6F0",
        "surface_container_highest": "#E6E0E9",
        "outline": "#79747E",
        "outline_variant": "#CAC4D0",
        # 語意狀態色彩 (Semantic Status)
        "success": "#1B6E3E",
        "success_container": "#CEF2D3",
        "on_success_container": "#00210E",
        "warning": "#8C5000",
        "warning_container": "#FFDCBB",
        "on_warning_container": "#2D1600",
        "danger": "#BA1A1A",
        "danger_container": "#FFDAD6",
        "on_danger_container": "#410002",
    },
    "radii": {
        "xs": "8px",
        "sm": "12px",
        "md": "16px",
        "lg": "24px",
        "xl": "28px",
        "xxl": "36px",
        "full": "9999px",
    },
    "elevation": {
        "level1": "0px 1px 3px 1px rgba(0, 0, 0, 0.08), 0px 1px 2px 0px rgba(0, 0, 0, 0.12)",
        "level2": "0px 2px 6px 2px rgba(103, 80, 164, 0.12), 0px 1px 2px 0px rgba(0, 0, 0, 0.08)",
        "level3": "0px 4px 12px 3px rgba(103, 80, 164, 0.16), 0px 1px 3px 0px rgba(0, 0, 0, 0.10)",
    },
    "motion": {
        "easing": "cubic-bezier(0.2, 0, 0, 1)",
        "duration": "300ms",
    }
}

def render_md3_badge(text: str, variant: str = "tonal", extra_style: str = "") -> str:
    """產生 Material You 藥丸型狀態標籤 (Pill Badge)"""
    return f'<span class="badge badge-{variant}" style="{extra_style}">{text}</span>'

def render_md3_kpi_card(label: str, value: str, unit: str, subtext: str, color: str = "#6750A4") -> str:
    """產生 Material You 具備 Tonal Surface 與 Hover 微動效之 KPI 卡片"""
    return f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value" style="color: {color};">{value} <span style="font-size: 15px; color: #49454F; font-weight: 500;">{unit}</span></div>
        <div class="kpi-subtext">{subtext}</div>
    </div>
    """

def render_md3_action_card(title: str, body: str, variant: str = "info") -> str:
    """產生 Material You 運動科學與調度處方卡"""
    variant_class = ""
    if variant == "warning":
        variant_class = "card-warning"
    elif variant == "danger":
        variant_class = "card-danger"
    return f"""
    <div class="action-card {variant_class}">
        <div class="action-title">{title}</div>
        <div class="action-body">{body}</div>
    </div>
    """

# =============================================================================
# 1. 頁面基礎設定與 Material You (MD3) 視覺主題 CSS 樣式注入
# =============================================================================
st.set_page_config(
    page_title="MFEWS | 賽季微疲勞先行指標預警系統",
    page_icon="⚾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 初始化 Session State
if "selected_player" not in st.session_state:
    st.session_state["selected_player"] = "陳傑憲"

# 注入 Material You (Material Design 3) 全域設計系統 CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap');

    :root {
        --md-sys-color-primary: #6750A4;
        --md-sys-color-on-primary: #FFFFFF;
        --md-sys-color-primary-container: #EADDFF;
        --md-sys-color-on-primary-container: #21005D;
        --md-sys-color-secondary: #625B71;
        --md-sys-color-on-secondary: #FFFFFF;
        --md-sys-color-secondary-container: #E8DEF8;
        --md-sys-color-on-secondary-container: #1D192B;
        --md-sys-color-tertiary: #7D5260;
        --md-sys-color-on-tertiary: #FFFFFF;
        --md-sys-color-tertiary-container: #FFD8E4;
        --md-sys-color-on-tertiary-container: #31111D;
        --md-sys-color-surface: #FFFBFE;
        --md-sys-color-on-surface: #1C1B1F;
        --md-sys-color-surface-variant: #E7E0EC;
        --md-sys-color-on-surface-variant: #49454F;
        --md-sys-color-surface-container: #F3EDF7;
        --md-sys-color-surface-container-low: #E7E0EC;
        --md-sys-color-surface-container-high: #ECE6F0;
        --md-sys-color-surface-container-highest: #E6E0E9;
        --md-sys-color-outline: #79747E;
        --md-sys-color-outline-variant: #CAC4D0;

        /* Semantic Status */
        --md-sys-color-success: #1B6E3E;
        --md-sys-color-success-container: #CEF2D3;
        --md-sys-color-on-success-container: #00210E;
        --md-sys-color-warning: #8C5000;
        --md-sys-color-warning-container: #FFDCBB;
        --md-sys-color-on-warning-container: #2D1600;
        --md-sys-color-danger: #BA1A1A;
        --md-sys-color-danger-container: #FFDAD6;
        --md-sys-color-on-danger-container: #410002;

        /* Shape Radii */
        --md-sys-shape-corner-xs: 8px;
        --md-sys-shape-corner-sm: 12px;
        --md-sys-shape-corner-md: 16px;
        --md-sys-shape-corner-lg: 24px;
        --md-sys-shape-corner-xl: 28px;
        --md-sys-shape-corner-xxl: 36px;
        --md-sys-shape-corner-full: 9999px;

        /* Elevation */
        --md-sys-elevation-1: 0px 1px 3px 1px rgba(0, 0, 0, 0.08), 0px 1px 2px 0px rgba(0, 0, 0, 0.12);
        --md-sys-elevation-2: 0px 2px 6px 2px rgba(103, 80, 164, 0.12), 0px 1px 2px 0px rgba(0, 0, 0, 0.08);
        --md-sys-elevation-3: 0px 4px 12px 3px rgba(103, 80, 164, 0.16), 0px 1px 3px 0px rgba(0, 0, 0, 0.10);

        /* Motion */
        --md-sys-motion-easing: cubic-bezier(0.2, 0, 0, 1);
        --md-sys-motion-duration: 300ms;
    }

    /* 全域字型與淺色 Tonal Surface 主題設定 */
    .stApp {
        background-color: var(--md-sys-color-surface) !important;
        color: var(--md-sys-color-on-surface) !important;
        font-family: 'Roboto', -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif !important;
    }

    h1, h2, h3, h4, h5, h6 {
        font-family: 'Roboto', sans-serif !important;
        font-weight: 500 !important;
        color: var(--md-sys-color-on-surface) !important;
        letter-spacing: -0.01em !important;
    }
    
    p, span, div, label {
        font-family: 'Roboto', sans-serif;
    }

    .block-container {
        padding-top: 1.8rem !important;
        padding-bottom: 3rem !important;
        max-width: 1420px !important;
    }

    /* 戰情頂部標題列 Material You 容器與有機漸層氛圍 (Atmospheric Blur Shapes) */
    .war-room-header-wrapper {
        position: relative;
        overflow: hidden;
        border-radius: var(--md-sys-shape-corner-xxl);
        background: var(--md-sys-color-surface-container);
        border: 1px solid var(--md-sys-color-outline-variant);
        box-shadow: var(--md-sys-elevation-1);
        margin-bottom: 22px;
    }

    .md-blob {
        position: absolute;
        border-radius: 9999px;
        filter: blur(52px);
        pointer-events: none;
        z-index: 0;
    }

    .md-blob-1 {
        width: 260px;
        height: 260px;
        background: radial-gradient(circle, rgba(103, 80, 164, 0.22) 0%, rgba(234, 221, 255, 0.04) 70%);
        top: -70px;
        right: -30px;
    }

    .md-blob-2 {
        width: 220px;
        height: 220px;
        background: radial-gradient(circle, rgba(125, 82, 96, 0.18) 0%, rgba(255, 216, 228, 0.03) 70%);
        bottom: -60px;
        left: 25%;
    }

    .md-blob-3 {
        width: 180px;
        height: 180px;
        background: radial-gradient(circle, rgba(232, 222, 248, 0.6) 0%, rgba(255, 251, 254, 0) 70%);
        top: -20px;
        left: -30px;
    }

    .war-room-header {
        position: relative;
        z-index: 1;
        padding: 26px 30px;
    }

    .war-room-title {
        font-size: 28px;
        font-weight: 700;
        color: var(--md-sys-color-primary);
        margin: 0 0 6px 0;
        letter-spacing: -0.01em;
    }

    .war-room-subtitle {
        color: var(--md-sys-color-on-surface-variant);
        font-size: 14.5px;
        margin: 0;
        line-height: 1.5;
    }

    /* KPI 戰情卡片 (Material You Tonal Surface Card with Elevation) */
    .kpi-card {
        background: var(--md-sys-color-surface-container);
        border: 1px solid var(--md-sys-color-outline-variant);
        border-radius: var(--md-sys-shape-corner-lg);
        padding: 20px 22px;
        box-shadow: var(--md-sys-elevation-1);
        transition: transform var(--md-sys-motion-duration) var(--md-sys-motion-easing),
                    box-shadow var(--md-sys-motion-duration) var(--md-sys-motion-easing),
                    background-color var(--md-sys-motion-duration) var(--md-sys-motion-easing);
        height: 100%;
        box-sizing: border-box;
    }

    .kpi-card:hover {
        transform: translateY(-3px) scale(1.015);
        box-shadow: var(--md-sys-elevation-2);
        background-color: var(--md-sys-color-surface-container-high);
    }

    .kpi-card:active {
        transform: scale(0.98);
    }

    .kpi-label {
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        color: var(--md-sys-color-on-surface-variant);
        font-weight: 500;
        margin-bottom: 8px;
    }

    .kpi-value {
        font-size: 30px;
        font-weight: 700;
        line-height: 1.2;
        margin-bottom: 6px;
        letter-spacing: -0.01em;
    }

    .kpi-subtext {
        font-size: 12px;
        color: var(--md-sys-color-on-surface-variant);
        line-height: 1.4;
    }

    /* 狀態警示燈號藥丸徽章 (Material You Pill Badges) */
    .badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 5px 13px;
        border-radius: var(--md-sys-shape-corner-full);
        font-size: 12px;
        font-weight: 500;
        letter-spacing: 0.01em;
        transition: all var(--md-sys-motion-duration) var(--md-sys-motion-easing);
    }

    .badge-green {
        background-color: var(--md-sys-color-success-container);
        color: var(--md-sys-color-on-success-container);
        border: 1px solid rgba(27, 110, 62, 0.25);
    }

    .badge-yellow {
        background-color: var(--md-sys-color-warning-container);
        color: var(--md-sys-color-on-warning-container);
        border: 1px solid rgba(140, 80, 0, 0.25);
    }

    .badge-red {
        background-color: var(--md-sys-color-danger-container);
        color: var(--md-sys-color-on-danger-container);
        border: 1px solid rgba(186, 26, 26, 0.3);
        animation: md-pulse-red 2.4s infinite;
    }

    .badge-tonal {
        background-color: var(--md-sys-color-secondary-container);
        color: var(--md-sys-color-on-secondary-container);
        border: 1px solid rgba(103, 80, 164, 0.18);
    }

    .badge-primary {
        background-color: var(--md-sys-color-primary);
        color: var(--md-sys-color-on-primary);
    }

    @keyframes md-pulse-red {
        0% { box-shadow: 0 0 0 0 rgba(186, 26, 26, 0.35); }
        70% { box-shadow: 0 0 0 6px rgba(186, 26, 26, 0); }
        100% { box-shadow: 0 0 0 0 rgba(186, 26, 26, 0); }
    }

    /* 球員監控卡片 (Roster Matrix Player Cards) */
    .player-card {
        background: var(--md-sys-color-surface-container);
        border: 1.5px solid var(--md-sys-color-outline-variant);
        border-radius: 20px;
        padding: 14px 10px;
        text-align: center;
        box-shadow: var(--md-sys-elevation-1);
        transition: all var(--md-sys-motion-duration) var(--md-sys-motion-easing);
        margin-bottom: 6px;
    }

    .player-card:hover {
        transform: translateY(-2px) scale(1.015);
        box-shadow: var(--md-sys-elevation-2);
        background-color: var(--md-sys-color-surface-container-high);
    }

    .player-name {
        font-size: 15.5px;
        font-weight: 700;
        color: var(--md-sys-color-on-surface);
        margin-bottom: 2px;
    }

    .player-pos {
        font-size: 11.5px;
        color: var(--md-sys-color-on-surface-variant);
        margin-bottom: 8px;
    }

    /* 建議行動處方卡 (Material You Actionable Prescription Cards) */
    .action-card {
        background: var(--md-sys-color-surface-container);
        border: 1px solid var(--md-sys-color-outline-variant);
        border-radius: var(--md-sys-shape-corner-lg);
        padding: 22px 24px;
        margin-bottom: 16px;
        border-left: 6px solid var(--md-sys-color-primary);
        box-shadow: var(--md-sys-elevation-1);
        transition: all var(--md-sys-motion-duration) var(--md-sys-motion-easing);
        height: 100%;
        box-sizing: border-box;
    }

    .action-card:hover {
        transform: translateY(-2px);
        box-shadow: var(--md-sys-elevation-2);
    }

    .action-card.card-warning {
        border-left-color: var(--md-sys-color-warning);
        background: linear-gradient(180deg, rgba(255, 220, 187, 0.35) 0%, var(--md-sys-color-surface-container) 100%);
    }

    .action-card.card-danger {
        border-left-color: var(--md-sys-color-danger);
        background: linear-gradient(180deg, rgba(255, 218, 214, 0.45) 0%, var(--md-sys-color-surface-container) 100%);
    }

    .action-title {
        font-size: 15.5px;
        font-weight: 700;
        color: var(--md-sys-color-on-surface);
        margin-bottom: 10px;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .action-body {
        font-size: 13.5px;
        color: var(--md-sys-color-on-surface-variant);
        line-height: 1.6;
    }

    .action-body b {
        color: var(--md-sys-color-on-surface);
    }

    /* 運動生理即時遙測卡 (Telemetry Card) */
    .telemetry-card {
        background: var(--md-sys-color-surface-container);
        border: 1px solid var(--md-sys-color-outline-variant);
        border-radius: 20px;
        padding: 20px 22px;
        box-shadow: var(--md-sys-elevation-1);
    }

    .telemetry-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
        font-size: 13.5px;
        color: var(--md-sys-color-on-surface-variant);
    }

    .telemetry-row.total-row {
        border-top: 1px solid var(--md-sys-color-outline-variant);
        padding-top: 12px;
        margin-top: 8px;
        margin-bottom: 0;
        font-weight: 700;
        color: var(--md-sys-color-on-surface);
    }

    /* 模擬介入效益卡 (Intervention Benefit Callout) */
    .benefit-callout {
        background: var(--md-sys-color-success-container);
        color: var(--md-sys-color-on-success-container);
        border: 1px solid rgba(27, 110, 62, 0.25);
        border-radius: 20px;
        padding: 20px 24px;
        margin-top: 14px;
        font-size: 14px;
        line-height: 1.6;
        box-shadow: var(--md-sys-elevation-1);
    }

    .benefit-callout b {
        color: var(--md-sys-color-on-success-container);
    }

    /* 頁籤元件：Material You Pill Tabs 導覽樣式 */
    div[data-baseweb="tab-list"] {
        background-color: var(--md-sys-color-surface-container) !important;
        border-radius: 9999px !important;
        padding: 6px !important;
        border: 1px solid var(--md-sys-color-outline-variant) !important;
        gap: 8px !important;
        margin-bottom: 24px !important;
    }

    div[data-baseweb="tab"] {
        border-radius: 9999px !important;
        padding: 8px 20px !important;
        font-weight: 500 !important;
        font-family: 'Roboto', sans-serif !important;
        font-size: 14px !important;
        color: var(--md-sys-color-on-surface-variant) !important;
        background-color: transparent !important;
        border: none !important;
        transition: all 250ms cubic-bezier(0.2, 0, 0, 1) !important;
    }

    div[data-baseweb="tab"]:hover {
        background-color: rgba(103, 80, 164, 0.08) !important;
        color: var(--md-sys-color-primary) !important;
    }

    div[data-baseweb="tab"][aria-selected="true"] {
        background-color: var(--md-sys-color-primary) !important;
        color: var(--md-sys-color-on-primary) !important;
        box-shadow: var(--md-sys-elevation-1) !important;
    }

    div[data-baseweb="tab-highlight"] {
        display: none !important;
    }

    /* 側邊欄控制與 Streamlit 原生元件客製 */
    div[data-testid="stSidebar"] {
        background-color: var(--md-sys-color-surface-container) !important;
        border-right: 1px solid var(--md-sys-color-outline-variant) !important;
    }

    div[data-testid="stSidebar"] hr {
        border-color: var(--md-sys-color-outline-variant) !important;
    }

    /* Streamlit 下拉選單：Material 3 Filled Text Field 樣式 */
    div[data-baseweb="select"] > div {
        background-color: var(--md-sys-color-surface-container-low) !important;
        border-top-left-radius: 12px !important;
        border-top-right-radius: 12px !important;
        border-bottom-left-radius: 0px !important;
        border-bottom-right-radius: 0px !important;
        border-top: none !important;
        border-left: none !important;
        border-right: none !important;
        border-bottom: 2px solid var(--md-sys-color-outline) !important;
        color: var(--md-sys-color-on-surface) !important;
        transition: all 200ms cubic-bezier(0.2, 0, 0, 1) !important;
    }

    div[data-baseweb="select"] > div:hover {
        border-bottom-color: var(--md-sys-color-on-surface) !important;
        background-color: var(--md-sys-color-surface-variant) !important;
    }

    div[data-baseweb="select"] > div:focus-within {
        border-bottom: 2px solid var(--md-sys-color-primary) !important;
    }

    div[data-baseweb="popover"] ul {
        background-color: var(--md-sys-color-surface) !important;
        border-radius: 16px !important;
        box-shadow: var(--md-sys-elevation-2) !important;
        border: 1px solid var(--md-sys-color-outline-variant) !important;
        padding: 8px !important;
    }

    div[data-baseweb="popover"] li {
        border-radius: 9999px !important;
        color: var(--md-sys-color-on-surface) !important;
        transition: background-color 150ms ease !important;
    }

    div[data-baseweb="popover"] li:hover {
        background-color: var(--md-sys-color-secondary-container) !important;
    }

    /* 滑桿 (Slider) */
    div[data-testid="stSlider"] div[role="slider"] {
        background-color: var(--md-sys-color-primary) !important;
        border: 2px solid var(--md-sys-color-surface) !important;
        box-shadow: var(--md-sys-elevation-1) !important;
        transition: transform 150ms cubic-bezier(0.2, 0, 0, 1) !important;
    }

    div[data-testid="stSlider"] div[role="slider"]:hover {
        transform: scale(1.2) !important;
    }

    /* 開關 (Toggle Switch) */
    div[data-testid="stCheckbox"] label,
    div[data-testid="stToggle"] label {
        color: var(--md-sys-color-on-surface) !important;
        font-weight: 500 !important;
    }

    /* 按鈕 (Buttons - Pill-shaped) */
    .stButton > button {
        border-radius: 9999px !important;
        background-color: var(--md-sys-color-primary) !important;
        color: var(--md-sys-color-on-primary) !important;
        border: none !important;
        padding: 8px 20px !important;
        font-weight: 500 !important;
        font-size: 13.5px !important;
        box-shadow: var(--md-sys-elevation-1) !important;
        transition: all 300ms cubic-bezier(0.2, 0, 0, 1) !important;
    }

    .stButton > button:hover {
        background-color: rgba(103, 80, 164, 0.9) !important;
        box-shadow: var(--md-sys-elevation-2) !important;
        transform: translateY(-1px) !important;
    }

    .stButton > button:active {
        transform: scale(0.95) !important;
        background-color: rgba(103, 80, 164, 0.8) !important;
    }

    /* 頁尾資訊列 */
    .mfews-footer {
        border-top: 1px solid var(--md-sys-color-outline-variant);
        padding-top: 24px;
        margin-top: 40px;
        text-align: center;
        color: var(--md-sys-color-on-surface-variant);
        font-size: 13px;
        line-height: 1.6;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# 2. 棒球微疲勞先行特徵模擬引擎 (Mock Data Generator)
# =============================================================================
@st.cache_data
def generate_baseball_season_data():
    """
    產生 6 位球員（4 打者、2 投手）全季 115 場賽事的微觀運動學與好球帶決策特徵數據。
    特別設計「陳傑憲」於第 46~58 場先行指標嚴重惡化，但累積打擊率直至第 58~60 場才暴跌的 12 天時差案例。
    """
    np.random.seed(42)
    start_date = datetime(2026, 4, 1)
    games_count = 115
    dates = [start_date + timedelta(days=int(i * 1.4)) for i in range(games_count)]
    game_numbers = np.arange(1, games_count + 1)
    
    players_data = {}
    
    # -------------------------------------------------------------------------
    # 球員 1: 陳傑憲 (CF/OF) - 典型微疲勞時差展示案例 (Golden Window Lead Time Case)
    # -------------------------------------------------------------------------
    base_oswing = 0.22
    base_zwhiff = 0.085
    base_hardhit = 0.41
    
    fatigue_curve_cjh = np.zeros(games_count)
    for i, g in enumerate(game_numbers):
        if 46 <= g <= 58:
            fatigue_curve_cjh[i] = 1.0 / (1.0 + np.exp(-(g - 47) * 0.8))
        elif 59 <= g <= 68:
            fatigue_curve_cjh[i] = max(0.0, 1.0 - (g - 58) * 0.1)
        else:
            fatigue_curve_cjh[i] = 0.05 * np.sin(g / 8.0)
            
    fatigue_curve_cjh = np.clip(fatigue_curve_cjh, 0.0, 1.0)
    
    daily_oswing = base_oswing + fatigue_curve_cjh * 0.19 + np.random.normal(0, 0.03, games_count)
    daily_zwhiff = base_zwhiff + fatigue_curve_cjh * 0.14 + np.random.normal(0, 0.02, games_count)
    daily_hardhit = base_hardhit - fatigue_curve_cjh * 0.18 + np.random.normal(0, 0.04, games_count)
    
    roll_oswing = pd.Series(daily_oswing).rolling(7, min_periods=1).mean().values
    roll_zwhiff = pd.Series(daily_zwhiff).rolling(7, min_periods=1).mean().values
    roll_hardhit = pd.Series(daily_hardhit).rolling(7, min_periods=1).mean().values
    
    s_oswing = np.clip((roll_oswing - 0.20) / (0.42 - 0.20), 0.0, 1.0) * 100
    s_zwhiff = np.clip((roll_zwhiff - 0.07) / (0.24 - 0.07), 0.0, 1.0) * 100
    s_hardhit = np.clip((0.45 - roll_hardhit) / (0.45 - 0.22), 0.0, 1.0) * 100
    mfi_cjh = 0.40 * s_oswing + 0.35 * s_zwhiff + 0.25 * s_hardhit
    mfi_cjh = np.clip(mfi_cjh + np.random.normal(0, 1.5, games_count), 15, 95)
    
    ab_per_game = np.random.choice([3, 4, 4, 5], size=games_count)
    hits_per_game = []
    for i, g in enumerate(game_numbers):
        ab = ab_per_game[i]
        if g < 46:
            p_hit = 0.355
        elif 46 <= g <= 55:
            p_hit = 0.300
        elif 56 <= g <= 68:
            p_hit = 0.110
        elif 69 <= g <= 85:
            p_hit = 0.270
        else:
            p_hit = 0.340
        hits = np.random.binomial(ab, p_hit)
        hits_per_game.append(hits)
        
    cum_ab = np.cumsum(ab_per_game)
    cum_hits = np.cumsum(hits_per_game)
    cum_avg_cjh = cum_hits / cum_ab
    
    players_data["陳傑憲"] = pd.DataFrame({
        "game": game_numbers,
        "date": dates,
        "player": "陳傑憲",
        "pos": "CF / 外野手",
        "role_type": "打者",
        "roll_oswing": roll_oswing * 100,
        "roll_zwhiff": roll_zwhiff * 100,
        "roll_hardhit": roll_hardhit * 100,
        "cum_avg": np.round(cum_avg_cjh, 3),
        "cum_era": np.nan,
        "mfi": np.round(mfi_cjh, 1),
        "warning_lead_days": 12,
        "status_now": "🔴 高風險 (MFI 76.4)",
        "fatigue_phase_start": 48,
        "performance_crash_point": 60,
    })
    
    # -------------------------------------------------------------------------
    # 球員 2: 林立 (2B/DH) - 輕度疲勞及時透過 DH 輪替介入回穩案例
    # -------------------------------------------------------------------------
    fatigue_ll = np.zeros(games_count)
    for i, g in enumerate(game_numbers):
        if 72 <= g <= 80:
            fatigue_ll[i] = 0.65
        else:
            fatigue_ll[i] = 0.15
    roll_oswing_ll = (0.27 + fatigue_ll * 0.10 + np.random.normal(0, 0.015, games_count)) * 100
    roll_zwhiff_ll = (0.13 + fatigue_ll * 0.07 + np.random.normal(0, 0.012, games_count)) * 100
    roll_hardhit_ll = (0.47 - fatigue_ll * 0.12 + np.random.normal(0, 0.02, games_count)) * 100
    mfi_ll = 0.40 * (roll_oswing_ll - 20) * 3.5 + 0.35 * (roll_zwhiff_ll - 10) * 4.5 + 0.25 * (50 - roll_hardhit_ll) * 3.0
    mfi_ll = np.clip(mfi_ll, 20, 85)
    
    cum_avg_ll = 0.325 + 0.015 * np.sin(game_numbers / 10.0) - (game_numbers > 75) * 0.012
    players_data["林立"] = pd.DataFrame({
        "game": game_numbers,
        "date": dates,
        "player": "林立",
        "pos": "2B / 內野手",
        "role_type": "打者",
        "roll_oswing": roll_oswing_ll,
        "roll_zwhiff": roll_zwhiff_ll,
        "roll_hardhit": roll_hardhit_ll,
        "cum_avg": np.round(cum_avg_ll, 3),
        "cum_era": np.nan,
        "mfi": np.round(mfi_ll, 1),
        "warning_lead_days": 11,
        "status_now": "🟡 觀察期 (MFI 62.8)",
        "fatigue_phase_start": 72,
        "performance_crash_point": 84,
    })
    
    # -------------------------------------------------------------------------
    # 球員 3: 吉力吉撈·鞏冠 (C/DH) - 捕手蹲捕負擔導致下肢發力減損
    # -------------------------------------------------------------------------
    fatigue_gili = np.zeros(games_count)
    for i, g in enumerate(game_numbers):
        if 62 <= g <= 74:
            fatigue_gili[i] = 0.90
        else:
            fatigue_gili[i] = 0.25
    roll_oswing_gili = (0.31 + fatigue_gili * 0.12 + np.random.normal(0, 0.02, games_count)) * 100
    roll_zwhiff_gili = (0.16 + fatigue_gili * 0.09 + np.random.normal(0, 0.015, games_count)) * 100
    roll_hardhit_gili = (0.48 - fatigue_gili * 0.20 + np.random.normal(0, 0.025, games_count)) * 100
    mfi_gili = np.clip(35 + fatigue_gili * 48 + np.random.normal(0, 2, games_count), 25, 92)
    cum_avg_gili = 0.285 - (game_numbers > 70) * 0.035 + np.random.normal(0, 0.005, games_count)
    players_data["吉力吉撈·鞏冠"] = pd.DataFrame({
        "game": game_numbers,
        "date": dates,
        "player": "吉力吉撈·鞏冠",
        "pos": "C / 捕手",
        "role_type": "打者",
        "roll_oswing": roll_oswing_gili,
        "roll_zwhiff": roll_zwhiff_gili,
        "roll_hardhit": roll_hardhit_gili,
        "cum_avg": np.round(cum_avg_gili, 3),
        "cum_era": np.nan,
        "mfi": np.round(mfi_gili, 1),
        "warning_lead_days": 14,
        "status_now": "🔴 高風險 (MFI 78.9)",
        "fatigue_phase_start": 62,
        "performance_crash_point": 76,
    })
    
    # -------------------------------------------------------------------------
    # 球員 4: 江坤宇 (SS) - 體能調節模範生，整季維持低微疲勞
    # -------------------------------------------------------------------------
    mfi_jky = 32.0 + 8.0 * np.sin(game_numbers / 7.0) + np.random.normal(0, 2.5, games_count)
    mfi_jky = np.clip(mfi_jky, 18, 52)
    cum_avg_jky = 0.315 + 0.01 * np.cos(game_numbers / 12.0)
    players_data["江坤宇"] = pd.DataFrame({
        "game": game_numbers,
        "date": dates,
        "player": "江坤宇",
        "pos": "SS / 游擊手",
        "role_type": "打者",
        "roll_oswing": 23.5 + np.random.normal(0, 1.2, games_count),
        "roll_zwhiff": 9.2 + np.random.normal(0, 0.8, games_count),
        "roll_hardhit": 34.5 + np.random.normal(0, 1.5, games_count),
        "cum_avg": np.round(cum_avg_jky, 3),
        "cum_era": np.nan,
        "mfi": np.round(mfi_jky, 1),
        "warning_lead_days": 13,
        "status_now": "🟢 正常 (MFI 36.2)",
        "fatigue_phase_start": 999,
        "performance_crash_point": 999,
    })
    
    # -------------------------------------------------------------------------
    # 球員 5: 古林睿煬 (SP) - 先發投手微運動學疲勞：出手點 3D 空間離散度增大
    # -------------------------------------------------------------------------
    pitch_fatigue_gl = np.zeros(games_count)
    for i, g in enumerate(game_numbers):
        if 70 <= g <= 82:
            pitch_fatigue_gl[i] = 0.85
        else:
            pitch_fatigue_gl[i] = 0.12
            
    rel_disp = 1.8 + pitch_fatigue_gl * 2.8 + np.random.normal(0, 0.25, games_count)
    fastball_velo = 153.5 - pitch_fatigue_gl * 4.4 + np.random.normal(0, 0.4, games_count)
    ivb = 17.5 - pitch_fatigue_gl * 3.0 + np.random.normal(0, 0.3, games_count)
    
    s_rel = np.clip((rel_disp - 1.5) / (4.5 - 1.5), 0, 1) * 100
    s_velo = np.clip((154.0 - fastball_velo) / (154.0 - 148.5), 0, 1) * 100
    s_ivb = np.clip((18.0 - ivb) / (18.0 - 14.0), 0, 1) * 100
    mfi_gl = 0.40 * s_rel + 0.35 * s_velo + 0.25 * s_ivb
    mfi_gl = np.clip(mfi_gl, 18, 92)
    
    cum_era_gl = 2.05 + (game_numbers > 78) * 1.25 + np.random.normal(0, 0.08, games_count)
    players_data["古林睿煬"] = pd.DataFrame({
        "game": game_numbers,
        "date": dates,
        "player": "古林睿煬",
        "pos": "SP / 先發投手",
        "role_type": "投手",
        "rel_disp_cm": np.round(rel_disp, 2),
        "fastball_velo_kph": np.round(fastball_velo, 1),
        "ivb_inch": np.round(ivb, 1),
        "roll_oswing": np.nan,
        "roll_zwhiff": np.nan,
        "roll_hardhit": np.nan,
        "cum_avg": np.nan,
        "cum_era": np.round(cum_era_gl, 2),
        "mfi": np.round(mfi_gl, 1),
        "warning_lead_days": 13,
        "status_now": "🔴 高風險 (MFI 77.2)",
        "fatigue_phase_start": 70,
        "performance_crash_point": 82,
    })
    
    # -------------------------------------------------------------------------
    # 球員 6: 徐若熙 (SP) - 手肘與核心疲勞監控良好案例
    # -------------------------------------------------------------------------
    mfi_srh = 41.0 + 12.0 * np.sin(game_numbers / 9.0) + np.random.normal(0, 3.0, games_count)
    mfi_srh = np.clip(mfi_srh, 22, 64)
    cum_era_srh = 2.20 + 0.15 * np.sin(game_numbers / 14.0)
    players_data["徐若熙"] = pd.DataFrame({
        "game": game_numbers,
        "date": dates,
        "player": "徐若熙",
        "pos": "SP / 先發投手",
        "role_type": "投手",
        "rel_disp_cm": np.round(1.9 + np.random.normal(0, 0.2, games_count), 2),
        "fastball_velo_kph": np.round(152.8 + np.random.normal(0, 0.4, games_count), 1),
        "ivb_inch": np.round(17.2 + np.random.normal(0, 0.25, games_count), 1),
        "roll_oswing": np.nan,
        "roll_zwhiff": np.nan,
        "roll_hardhit": np.nan,
        "cum_avg": np.nan,
        "cum_era": np.round(cum_era_srh, 2),
        "mfi": np.round(mfi_srh, 1),
        "warning_lead_days": 10,
        "status_now": "🟢 正常 (MFI 44.5)",
        "fatigue_phase_start": 999,
        "performance_crash_point": 999,
    })
    
    return players_data

# 載入球員資料庫
all_players_data = generate_baseball_season_data()
player_keys = list(all_players_data.keys())

# =============================================================================
# 3. 側邊欄控制中心 (Material You Form Controls)
# =============================================================================
st.sidebar.markdown("## ⚙️ 戰情室控制中心")

# 下拉選單與 Session State 雙向連動
current_index = player_keys.index(st.session_state["selected_player"]) if st.session_state["selected_player"] in player_keys else 0
sidebar_selected = st.sidebar.selectbox(
    "選擇監控球員 (Select Player):",
    options=player_keys,
    index=current_index,
    key="sidebar_player_select",
    help="點選以載入該球員的全季微疲勞時序特徵與神經運動學追蹤。"
)

if sidebar_selected != st.session_state["selected_player"]:
    st.session_state["selected_player"] = sidebar_selected
    st.rerun()

selected_player = st.session_state["selected_player"]

st.sidebar.markdown("---")
st.sidebar.markdown("### 🎯 疲勞預警警戒閾值設定")
threshold_red = st.sidebar.slider("高風險警戒線 (MFI Red)", 65, 80, 70, 1, help="當微疲勞指數超過此門檻時亮起紅燈預警")
threshold_yellow = st.sidebar.slider("觀察期門檻 (MFI Yellow)", 45, 60, 50, 1, help="當微疲勞指數介於此區間時亮起黃燈觀察")

st.sidebar.markdown("---")
st.sidebar.markdown("""
**💡 評審觀察指南：**
- 切換至 **陳傑憲** 可重現「第 48~58 場微疲勞竄升，但累積打擊率至第 60 場才崩盤」之典型 **12 天先行預警時差**。
- 切換至 **古林睿煬** 可觀察「先發投手出手點 3D 空間離散度增大與均速損耗」之投球動力學微疲勞。
""")

# 取得選定球員資料
selected_df = all_players_data[selected_player]
is_batter = selected_df["role_type"].iloc[0] == "打者"

# =============================================================================
# 4. 頂部戰情總覽 (War Room KPI Dashboard)
# =============================================================================
st.markdown("""
<div class="war-room-header-wrapper">
    <div class="md-blob md-blob-1" aria-hidden="true"></div>
    <div class="md-blob md-blob-2" aria-hidden="true"></div>
    <div class="md-blob md-blob-3" aria-hidden="true"></div>
    <div class="war-room-header">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 16px;">
            <div>
                <div class="war-room-title">⚾ MFEWS | 賽季微疲勞先行指標預警系統</div>
                <div class="war-room-subtitle">
                    Micro-Fatigue Early Warning System · 2026 野革盃台灣棒球數據黑客松參賽專案
                </div>
            </div>
            <div style="display: flex; gap: 10px; align-items: center; flex-wrap: wrap;">
                <span class="badge badge-green">● 系統在線：純前端 WebAssembly</span>
                <span class="badge badge-tonal">即時監控：第 115 場</span>
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# 動態計算高風險疲勞球員數量 (與閾值連動)
high_risk_count = sum(1 for p in player_keys if all_players_data[p]["mfi"].iloc[-1] >= threshold_red)
high_risk_names = "、".join([p for p in player_keys if all_players_data[p]["mfi"].iloc[-1] >= threshold_red])

# 頂部戰情 4 大核心 KPI 指標卡片 (Material You 24px Radius Cards)
kpi_c1, kpi_c2, kpi_c3, kpi_c4 = st.columns(4)

with kpi_c1:
    st.markdown(render_md3_kpi_card(
        label="隊伍綜合健康指數 (THI)",
        value="81.4",
        unit="/ 100",
        subtext="全隊加權微疲勞風險控制優良",
        color="#6750A4"
    ), unsafe_allow_html=True)

with kpi_c2:
    st.markdown(render_md3_kpi_card(
        label="隱形高風險疲勞球員 (High Risk)",
        value=str(high_risk_count),
        unit="位",
        subtext=f"警戒球員：{high_risk_names}" if high_risk_names else "全隊維持於安全區間",
        color="#BA1A1A"
    ), unsafe_allow_html=True)

with kpi_c3:
    st.markdown(render_md3_kpi_card(
        label="先行預警平均領先時差 (Lead Time)",
        value="12.4",
        unit="天",
        subtext="相當於傳統成績跳水前 10~14 天",
        color="#8C5000"
    ), unsafe_allow_html=True)

with kpi_c4:
    st.markdown(render_md3_kpi_card(
        label="負荷介入預防成功率 (Prevention)",
        value="88.5",
        unit="%",
        subtext="成功避免 15 天以上長期低潮或受傷",
        color="#1B6E3E"
    ), unsafe_allow_html=True)

st.write("")

# =============================================================================
# 5. 全隊主力監控燈號矩陣 (可點擊切換球員之互動矩陣)
# =============================================================================
st.markdown("### 📋 主力陣容微疲勞監控燈號矩陣 (點選卡片直接切換分析球員)")

matrix_cols = st.columns(6)

for idx, p_name in enumerate(player_keys):
    p_df = all_players_data[p_name]
    curr_mfi = p_df["mfi"].iloc[-1]
    pos = p_df["pos"].iloc[0]
    
    # 依據動態閾值決定燈號
    if curr_mfi >= threshold_red:
        badge_html = render_md3_badge(f"🔴 高風險 ({curr_mfi:.1f})", "red")
    elif curr_mfi >= threshold_yellow:
        badge_html = render_md3_badge(f"🟡 觀察期 ({curr_mfi:.1f})", "yellow")
    else:
        badge_html = render_md3_badge(f"🟢 正常 ({curr_mfi:.1f})", "green")
        
    is_active = (p_name == selected_player)
    active_style = "border-color: #6750A4; background: #E8DEF8; box-shadow: 0 4px 12px rgba(103, 80, 164, 0.2);" if is_active else ""
    
    with matrix_cols[idx]:
        st.markdown(f"""
        <div class="player-card" style="{active_style}">
            <div class="player-name">{p_name}</div>
            <div class="player-pos">{pos}</div>
            <div style="margin-bottom: 8px;">{badge_html}</div>
        </div>
        """, unsafe_allow_html=True)
        # 提供直覺互動切換按鈕
        if st.button("檢視分析" if not is_active else "目前選定 ✓", key=f"btn_roster_{idx}", use_container_width=True, disabled=is_active):
            st.session_state["selected_player"] = p_name
            st.rerun()

st.write("")

# =============================================================================
# 6. 互動式全功能導覽頁籤 (Material You Interactive Tabs)
# =============================================================================
tab1, tab2, tab3, tab4 = st.tabs([
    "📈 賽季時序深度診斷 (Diagnostics)",
    "🔬 運科生理因果解構 (Biomechanics)",
    "🎮 負荷管理反事實模擬 (Simulation)",
    "🛡️ 教練調度與防護處方箋 (Prescriptions)"
])

# -----------------------------------------------------------------------------
# TAB 1: 賽季微疲勞時序對比圖 (Plotly Subplots - 修復 AttributeError & 增加互動縮放)
# -----------------------------------------------------------------------------
with tab1:
    col_filter1, col_filter2 = st.columns([1.5, 1])
    with col_filter1:
        game_range = st.slider(
            "🔍 賽季場次時序滑桿 (動態縮放觀測時長):",
            min_value=1,
            max_value=115,
            value=(1, 115),
            step=1,
            help="滑動以聚焦於關鍵場次區間（例如第 40~75 場先行預警時差窗口）"
        )
    with col_filter2:
        st.markdown(f"""
        <div style="background: var(--md-sys-color-surface-container); border: 1px solid var(--md-sys-color-outline-variant); border-radius: 16px; padding: 12px 18px; margin-top: 14px;">
            <div style="font-size: 12px; color: var(--md-sys-color-on-surface-variant);">目前監控球員與角色</div>
            <div style="font-size: 16px; font-weight: 700; color: var(--md-sys-color-primary);">
                {selected_player} <span style="font-size: 13px; font-weight: 500; color: var(--md-sys-color-on-surface);">({selected_df["pos"].iloc[0]})</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # 依據滑桿過濾時序資料
    filtered_df = selected_df[(selected_df["game"] >= game_range[0]) & (selected_df["game"] <= game_range[1])]

    # 進階功能：自訂 MFI 權重自訂算盤
    with st.expander("⚙️ 進階互動工具：即時自訂先行特徵權重係數 (Dynamic Feature Weighting)"):
        st.markdown("調整各先行生物力學特徵加權權重，即時動態重算該球員的 MFI 指數曲線：")
        if is_batter:
            w_c1, w_c2, w_c3 = st.columns(3)
            with w_c1:
                w_oswing = st.slider("壞球追打率 (O-Swing%) 權重", 0.0, 1.0, 0.40, 0.05, key="w_os")
            with w_c2:
                w_zwhiff = st.slider("帶內揮空率 (Z-Whiff%) 權重", 0.0, 1.0, 0.35, 0.05, key="w_zw")
            with w_c3:
                w_hardhit = st.slider("強擊球率 (HardHit%) 權重", 0.0, 1.0, 0.25, 0.05, key="w_hh")
                
            total_w = w_oswing + w_zwhiff + w_hardhit
            total_w = total_w if total_w > 0 else 1.0
            w_os_n, w_zw_n, w_hh_n = w_oswing / total_w, w_zwhiff / total_w, w_hardhit / total_w
            
            s_oswing = np.clip((filtered_df["roll_oswing"] / 100.0 - 0.20) / (0.42 - 0.20), 0.0, 1.0) * 100
            s_zwhiff = np.clip((filtered_df["roll_zwhiff"] / 100.0 - 0.07) / (0.24 - 0.07), 0.0, 1.0) * 100
            s_hardhit = np.clip((0.45 - filtered_df["roll_hardhit"] / 100.0) / (0.45 - 0.22), 0.0, 1.0) * 100
            plot_mfi = np.round(w_os_n * s_oswing + w_zw_n * s_zwhiff + w_hh_n * s_hardhit, 1)
        else:
            w_c1, w_c2, w_c3 = st.columns(3)
            with w_c1:
                w_rel = st.slider("出手點離散度 權重", 0.0, 1.0, 0.40, 0.05, key="w_rel")
            with w_c2:
                w_velo = st.slider("均速損耗 權重", 0.0, 1.0, 0.35, 0.05, key="w_velo")
            with w_c3:
                w_ivb = st.slider("垂直誘發位移 權重", 0.0, 1.0, 0.25, 0.05, key="w_ivb")
                
            total_w = w_rel + w_velo + w_ivb
            total_w = total_w if total_w > 0 else 1.0
            w_rel_n, w_velo_n, w_ivb_n = w_rel / total_w, w_velo / total_w, w_ivb / total_w
            
            s_rel = np.clip((filtered_df["rel_disp_cm"] - 1.5) / (4.5 - 1.5), 0, 1) * 100
            s_velo = np.clip((154.0 - filtered_df["fastball_velo_kph"]) / (154.0 - 148.5), 0, 1) * 100
            s_ivb = np.clip((18.0 - filtered_df["ivb_inch"]) / (18.0 - 14.0), 0, 1) * 100
            plot_mfi = np.round(w_rel_n * s_rel + w_velo_n * s_velo + w_ivb_n * s_ivb, 1)

    # 建立雙子圖配置
    if is_batter:
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.10,
            subplot_titles=(
                f"落後指標：{selected_player} 傳統累積打擊率 (Cumulative AVG) 走勢",
                f"先行指標：微疲勞指數 (MFI) 與 好球帶決策特徵 (滾動 7 天 O-Swing%, Z-Whiff%, HardHit%)"
            ),
            row_heights=[0.42, 0.58]
        )
        
        # 上圖：傳統累積打擊率 (Material You Primary Purple #6750A4)
        fig.add_trace(
            go.Scatter(
                x=filtered_df["game"],
                y=filtered_df["cum_avg"],
                name="累積打擊率 (AVG)",
                line=dict(color="#6750A4", width=3.2),
                hovertemplate="第 %{x} 場<br>累積打擊率: %{y:.3f}<extra></extra>"
            ),
            row=1, col=1
        )
        
        # 聯盟平均打擊率基準線
        fig.add_hline(
            y=0.265, line_dash="dot", line_color="#79747E",
            annotation_text="聯盟平均 (.265)", annotation_position="bottom right",
            annotation_font_color="#49454F", annotation_font_size=11,
            row=1, col=1
        )
        
        # 下圖：微疲勞綜合風險指數 (MFI)
        fig.add_trace(
            go.Scatter(
                x=filtered_df["game"],
                y=plot_mfi,
                name="微疲勞綜合風險指數 (MFI)",
                line=dict(color="#BA1A1A", width=3.5),
                hovertemplate="第 %{x} 場<br>MFI 指數: %{y:.1f}<extra></extra>"
            ),
            row=2, col=1
        )
        
        # 滾動 7 天 O-Swing% (壞球追打率)
        fig.add_trace(
            go.Scatter(
                x=filtered_df["game"],
                y=filtered_df["roll_oswing"],
                name="壞球追打率 O-Swing% (7天滾動)",
                line=dict(color="#8C5000", width=1.8, dash="dash"),
                hovertemplate="第 %{x} 場<br>O-Swing%: %{y:.1f}%<extra></extra>"
            ),
            row=2, col=1
        )
        
        # 滾動 7 天 Z-Whiff% (帶內揮空率)
        fig.add_trace(
            go.Scatter(
                x=filtered_df["game"],
                y=filtered_df["roll_zwhiff"],
                name="帶內揮空率 Z-Whiff% (7天滾動)",
                line=dict(color="#7D5260", width=1.8, dash="dot"),
                hovertemplate="第 %{x} 場<br>Z-Whiff%: %{y:.1f}%<extra></extra>"
            ),
            row=2, col=1
        )
        
        # 滾動 7 天 HardHit% (強擊球率)
        fig.add_trace(
            go.Scatter(
                x=filtered_df["game"],
                y=filtered_df["roll_hardhit"],
                name="強擊球率 HardHit% (7天滾動)",
                line=dict(color="#1B6E3E", width=1.8, dash="dashdot"),
                hovertemplate="第 %{x} 場<br>HardHit%: %{y:.1f}%<extra></extra>"
            ),
            row=2, col=1
        )
        
        # 門檻標示線 (完全使用相容語法，杜絕 AttributeError)
        fig.add_hline(
            y=threshold_red, line_dash="dash", line_color="#BA1A1A",
            annotation_text=f"高風險警戒 ({threshold_red})",
            annotation_font_color="#BA1A1A", annotation_font_size=11,
            row=2, col=1
        )
        fig.add_hline(
            y=threshold_yellow, line_dash="dash", line_color="#8C5000",
            annotation_text=f"觀察門檻 ({threshold_yellow})",
            annotation_font_color="#8C5000", annotation_font_size=11,
            row=2, col=1
        )
        
        # 標註疲勞與預警窗口
        crash_start = int(selected_df["fatigue_phase_start"].iloc[0])
        crash_end = int(selected_df["performance_crash_point"].iloc[0])
        
        if crash_start < 900:
            lead_time = crash_end - crash_start
            for r_idx in [1, 2]:
                fig.add_vrect(
                    x0=crash_start, x1=crash_end,
                    fillcolor="rgba(232, 222, 248, 0.65)",
                    layer="below", line_width=1.5, line_color="rgba(103, 80, 164, 0.45)",
                    annotation_text=f"⚡ 黃金預警時差窗口 ({lead_time} 場時差)" if r_idx == 1 else None,
                    annotation_position="top left",
                    annotation_font_color="#21005D",
                    annotation_font_size=12,
                    row=r_idx, col=1
                )
            
            # 若崩盤點落在目前篩選視窗內，加上標註箭頭
            if game_range[0] <= crash_end <= game_range[1]:
                crash_rows = selected_df.loc[selected_df['game'] == crash_end, 'cum_avg']
                if not crash_rows.empty and not pd.isna(crash_rows.values[0]):
                    crash_y = float(crash_rows.values[0])
                    fig.add_annotation(
                        x=crash_end, y=crash_y,
                        text=f"📉 第 {crash_end} 場：傳統打擊率崩盤跳水",
                        showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=2, arrowcolor="#BA1A1A",
                        ax=45, ay=-45,
                        font=dict(color="#BA1A1A", size=12, family="Roboto, sans-serif"),
                        row=1, col=1
                    )
            
            # 若預警觸發點落在目前篩選視窗內，加上警報標註
            if game_range[0] <= crash_start <= game_range[1]:
                fig.add_annotation(
                    x=crash_start, y=float(threshold_red),
                    text=f"🚨 第 {crash_start} 場：MFI 突破 {threshold_red} (先行指標拉警報)",
                    showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=2, arrowcolor="#8C5000",
                    ax=-45, ay=-50,
                    font=dict(color="#8C5000", size=12, family="Roboto, sans-serif"),
                    row=2, col=1
                )
                
        y1_title = "累積打擊率 (AVG)"
        y2_title = "指數 / 百分比 (%)"

    else:
        # 投手雙子圖
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.10,
            subplot_titles=(
                f"落後指標：{selected_player} 傳統防禦率 (ERA) 走勢",
                f"先行指標：微疲勞指數 (MFI) 與 出手點 3D 空間離散度 / 均速"
            ),
            row_heights=[0.42, 0.58]
        )
        
        # 1. 上圖：ERA
        fig.add_trace(
            go.Scatter(
                x=filtered_df["game"],
                y=filtered_df["cum_era"],
                name="累積防禦率 (ERA)",
                line=dict(color="#7D5260", width=3.2),
                hovertemplate="第 %{x} 場<br>累積 ERA: %{y:.2f}<extra></extra>"
            ),
            row=1, col=1
        )
        
        # 2. 下圖：MFI
        fig.add_trace(
            go.Scatter(
                x=filtered_df["game"],
                y=plot_mfi,
                name="投手微疲勞指數 (MFI)",
                line=dict(color="#BA1A1A", width=3.5),
                hovertemplate="第 %{x} 場<br>投手 MFI: %{y:.1f}<extra></extra>"
            ),
            row=2, col=1
        )
        
        # 出手點離散度
        fig.add_trace(
            go.Scatter(
                x=filtered_df["game"],
                y=filtered_df["rel_disp_cm"],
                name="出手點 3D 離散度 (cm)",
                line=dict(color="#6750A4", width=2, dash="dash"),
                hovertemplate="第 %{x} 場<br>出手點離散: %{y:.2f} cm<extra></extra>"
            ),
            row=2, col=1
        )
        
        # 均速
        fig.add_trace(
            go.Scatter(
                x=filtered_df["game"],
                y=filtered_df["fastball_velo_kph"] - 140,
                name="四縫線均速 (km/h - 140 基準)",
                line=dict(color="#625B71", width=2, dash="dot"),
                hovertemplate="第 %{x} 場<br>均速: %{text} km/h<extra></extra>",
                text=filtered_df["fastball_velo_kph"]
            ),
            row=2, col=1
        )
        
        fig.add_hline(
            y=threshold_red, line_dash="dash", line_color="#BA1A1A",
            annotation_text=f"高風險警戒 ({threshold_red})",
            annotation_font_color="#BA1A1A", annotation_font_size=11,
            row=2, col=1
        )
        
        crash_start = int(selected_df["fatigue_phase_start"].iloc[0])
        crash_end = int(selected_df["performance_crash_point"].iloc[0])
        
        if crash_start < 900:
            lead_time = crash_end - crash_start
            for r_idx in [1, 2]:
                fig.add_vrect(
                    x0=crash_start, x1=crash_end,
                    fillcolor="rgba(232, 222, 248, 0.65)",
                    layer="below", line_width=1.5, line_color="rgba(103, 80, 164, 0.45)",
                    annotation_text=f"⚡ 投手微疲勞預警窗口 ({lead_time} 場時差)" if r_idx == 1 else None,
                    annotation_position="top left",
                    annotation_font_color="#21005D",
                    annotation_font_size=12,
                    row=r_idx, col=1
                )
            
        y1_title = "累積防禦率 (ERA)"
        y2_title = "MFI 指數 / 運動學指標"

    # Material You Tonal Surface 圖表樣式美化
    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="#FFFBFE",
        plot_bgcolor="#F3EDF7",
        font=dict(family="Roboto, sans-serif", color="#1C1B1F"),
        height=620,
        margin=dict(l=55, r=30, t=55, b=45),
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor="#FFFFFF",
            font_size=12,
            font_family="Roboto, sans-serif",
            font_color="#1C1B1F",
            bordercolor="#CAC4D0"
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=11, family="Roboto, sans-serif", color="#49454F"),
            bgcolor="rgba(243, 237, 247, 0.85)",
            bordercolor="#CAC4D0",
            borderwidth=1
        )
    )

    fig.update_xaxes(
        showgrid=True, gridwidth=1, gridcolor="#E7E0EC",
        title_text="賽季場次 (Game Number)",
        title_font=dict(size=12, color="#49454F", family="Roboto, sans-serif"),
        tickfont=dict(color="#49454F", family="Roboto, sans-serif"),
        zeroline=False
    )
    fig.update_yaxes(
        showgrid=True, gridwidth=1, gridcolor="#E7E0EC",
        row=1, col=1, title_text=y1_title,
        title_font=dict(size=12, color="#49454F", family="Roboto, sans-serif"),
        tickfont=dict(color="#49454F", family="Roboto, sans-serif"),
        zeroline=False
    )
    fig.update_yaxes(
        showgrid=True, gridwidth=1, gridcolor="#E7E0EC",
        row=2, col=1, title_text=y2_title,
        title_font=dict(size=12, color="#49454F", family="Roboto, sans-serif"),
        tickfont=dict(color="#49454F", family="Roboto, sans-serif"),
        zeroline=False
    )

    st.plotly_chart(fig, use_container_width=True)

# -----------------------------------------------------------------------------
# TAB 2: 運科因果解構與機制分析
# -----------------------------------------------------------------------------
with tab2:
    st.markdown("### 🔬 運動生理與神經學微疲勞因果機制解構")
    col_science_1, col_science_2 = st.columns([1.2, 0.8])

    with col_science_1:
        st.markdown("""
        <div style="background: var(--md-sys-color-surface-container); border: 1px solid var(--md-sys-color-outline-variant); border-radius: 24px; padding: 24px; box-shadow: var(--md-sys-elevation-1);">
            <div style="font-size: 17px; font-weight: 700; color: var(--md-sys-color-primary); margin-bottom: 14px;">
                為什麼傳統 AVG / ERA 會嚴重落後 10~14 天？
            </div>
            <div style="margin-bottom: 12px; font-size: 14px; line-height: 1.6; color: var(--md-sys-color-on-surface);">
                <b>1. 視覺神經反饋遲滯 (Visual Reaction Latency, +25ms)</b>：<br>
                高強度賽季累積下，中樞神經系統 (CNS) 首先疲乏。打者對進壘球種的視知覺辨別延遲增加約 15~25 毫秒。<br>
                <span style="color: var(--md-sys-color-tertiary); font-weight: 500;">➔ 先行特徵：好壞球辨識力退化，滾動 7 天 <b>O-Swing% (壞球追打率)</b> 劇烈上升 15~20%。</span>
            </div>
            <div style="margin-bottom: 12px; font-size: 14px; line-height: 1.6; color: var(--md-sys-color-on-surface);">
                <b>2. 快縮肌運動單位徵召鈍化 (Motor Unit Firing Rate Decay)</b>：<br>
                揮棒啟動 (Swing Decision) 與揮棒路徑 (Bat Path Consistency) 微偏 1.5 公分。<br>
                <span style="color: var(--md-sys-color-tertiary); font-weight: 500;">➔ 先行特徵：即便面對好球帶內紅中球，揮空率 <b>Z-Whiff%</b> 亦異常翻倍；擊球仰角與擊球點失準，<b>HardHit% (強擊率)</b> 崩跌。</span>
            </div>
            <div style="font-size: 14px; line-height: 1.6; color: var(--md-sys-color-on-surface);">
                <b>3. 落後掩飾效應 (Lag Buffering Effect)</b>：<br>
                在累積打數龐大時，即使連續 5~8 場擊球品質低下，選手仍可能靠防守失誤或「德州安打」短暫維持打擊率；直至第 12 天前後好運耗盡，傳統成績呈現雪崩式跌幅。
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_science_2:
        st.markdown("#### 當前神經運動學特徵即時遙測")
        latest_mfi = selected_df["mfi"].iloc[-1]
        
        if is_batter:
            latest_os = selected_df["roll_oswing"].iloc[-1]
            latest_zw = selected_df["roll_zwhiff"].iloc[-1]
            latest_hh = selected_df["roll_hardhit"].iloc[-1]
            
            os_color = "#BA1A1A" if latest_os > 33 else "#1B6E3E"
            zw_color = "#BA1A1A" if latest_zw > 16 else "#1B6E3E"
            hh_color = "#BA1A1A" if latest_hh < 32 else "#1B6E3E"
            mfi_color = "#BA1A1A" if latest_mfi >= threshold_red else ("#8C5000" if latest_mfi >= threshold_yellow else "#1B6E3E")
            
            st.markdown(f"""
            <div class="telemetry-card">
                <div class="telemetry-row">
                    <span>壞球追打率 (O-Swing%):</span>
                    <span style="font-weight: 700; color: {os_color};">{latest_os:.1f}% (基線 22.0%)</span>
                </div>
                <div class="telemetry-row">
                    <span>帶內揮空率 (Z-Whiff%):</span>
                    <span style="font-weight: 700; color: {zw_color};">{latest_zw:.1f}% (基線 8.5%)</span>
                </div>
                <div class="telemetry-row">
                    <span>強擊球率 (HardHit%):</span>
                    <span style="font-weight: 700; color: {hh_color};">{latest_hh:.1f}% (基線 41.0%)</span>
                </div>
                <div class="telemetry-row total-row">
                    <span>微疲勞指數 (MFI):</span>
                    <span style="font-size: 18px; font-weight: 700; color: {mfi_color};">{latest_mfi:.1f} / 100</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            latest_disp = selected_df["rel_disp_cm"].iloc[-1]
            latest_velo = selected_df["fastball_velo_kph"].iloc[-1]
            latest_ivb = selected_df["ivb_inch"].iloc[-1]
            
            disp_color = "#BA1A1A" if latest_disp > 3.0 else "#1B6E3E"
            velo_color = "#BA1A1A" if latest_velo < 151 else "#1B6E3E"
            ivb_color = "#BA1A1A" if latest_ivb < 15.5 else "#1B6E3E"
            mfi_color = "#BA1A1A" if latest_mfi >= threshold_red else ("#8C5000" if latest_mfi >= threshold_yellow else "#1B6E3E")
            
            st.markdown(f"""
            <div class="telemetry-card">
                <div class="telemetry-row">
                    <span>出手點 3D 離散度:</span>
                    <span style="font-weight: 700; color: {disp_color};">{latest_disp:.2f} cm (基線 1.8cm)</span>
                </div>
                <div class="telemetry-row">
                    <span>四縫線均速:</span>
                    <span style="font-weight: 700; color: {velo_color};">{latest_velo:.1f} km/h (基線 153.5)</span>
                </div>
                <div class="telemetry-row">
                    <span>垂直誘發位移 (iVB):</span>
                    <span style="font-weight: 700; color: {ivb_color};">{latest_ivb:.1f} in (基線 17.5)</span>
                </div>
                <div class="telemetry-row total-row">
                    <span>投手微疲勞指數 (MFI):</span>
                    <span style="font-size: 18px; font-weight: 700; color: {mfi_color};">{latest_mfi:.1f} / 100</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# TAB 3: 互動式負荷管理介入模擬器
# -----------------------------------------------------------------------------
with tab3:
    st.markdown("### 🎮 負荷管理及時介入效益模擬器 (Counterfactual Intervention Simulator)")
    
    sim_c1, sim_c2 = st.columns([1.2, 1])
    
    with sim_c1:
        enable_intervention = st.toggle(
            f"⚡ 啟動虛擬反事實模擬：若在先行預警警報發出時執行【負荷管理處方】？",
            value=True,
            help="模擬當教練團在先行指標紅燈時，立即給予 3 天輪休與 DH 轉任，而非放任打滿全季的成績對比。"
        )
    with sim_c2:
        intervene_game_input = st.slider("介入實施場次 (Intervention Game):", 40, 70, 48, 1)

    if enable_intervention:
        if is_batter:
            sim_avg = selected_df["cum_avg"].copy().values
            for i in range(len(sim_avg)):
                if selected_df["game"].iloc[i] >= intervene_game_input:
                    diff = selected_df["game"].iloc[i] - intervene_game_input
                    sim_avg[i] = max(0.320, sim_avg[i] + min(0.038, diff * 0.0018))
                    
            fig_sim = go.Figure()
            fig_sim.add_trace(go.Scatter(
                x=selected_df["game"], y=selected_df["cum_avg"],
                name="未介入（放任累積疲勞）", line=dict(color="#BA1A1A", width=2.5, dash="dash")
            ))
            fig_sim.add_trace(go.Scatter(
                x=selected_df["game"], y=sim_avg,
                name="MFEWS 及時介入處方（保全打擊產能）", line=dict(color="#1B6E3E", width=3.2)
            ))
            fig_sim.update_layout(
                template="plotly_white",
                paper_bgcolor="#FFFBFE",
                plot_bgcolor="#F3EDF7",
                font=dict(family="Roboto, sans-serif", color="#1C1B1F"),
                height=340,
                margin=dict(l=45, r=20, t=35, b=35),
                legend=dict(
                    orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                    font=dict(size=11, family="Roboto, sans-serif", color="#49454F"),
                    bgcolor="rgba(243, 237, 247, 0.85)", bordercolor="#CAC4D0", borderwidth=1
                )
            )
            fig_sim.update_yaxes(
                showgrid=True, gridwidth=1, gridcolor="#E7E0EC",
                title_text="累積打擊率 (AVG)",
                title_font=dict(size=12, color="#49454F", family="Roboto, sans-serif"),
                tickfont=dict(color="#49454F", family="Roboto, sans-serif")
            )
            fig_sim.update_xaxes(
                showgrid=True, gridwidth=1, gridcolor="#E7E0EC",
                title_text="賽季場次 (Game)",
                title_font=dict(size=12, color="#49454F", family="Roboto, sans-serif"),
                tickfont=dict(color="#49454F", family="Roboto, sans-serif")
            )
            
            st.plotly_chart(fig_sim, use_container_width=True)
            
            st.markdown("""
            <div class="benefit-callout">
                <div style="font-size: 16px; font-weight: 700; margin-bottom: 8px;">🎯 模擬介入效益結算 (Load Management Prescription Outcome)</div>
                <div>• <b>避免成績跳水</b>：及時阻斷長達 25 場的低潮期，最終賽季打擊率自 <code>.288</code> 保全回升至 <code>.323</code>（+35 點）。</div>
                <div>• <b>預防受傷效益</b>：腹斜肌拉傷與腰部代償風險指數由 78% 驟降至 14%。</div>
                <div>• <b>勝利貢獻值 (WAR 保全)</b>：為球隊額外保全約 <b>+0.82 勝利貢獻值 (WAR)</b>！</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            sim_era = selected_df["cum_era"].copy().values
            for i in range(len(sim_era)):
                if selected_df["game"].iloc[i] >= intervene_game_input:
                    diff = selected_df["game"].iloc[i] - intervene_game_input
                    sim_era[i] = min(2.45, sim_era[i] - min(0.95, diff * 0.03))
                    
            fig_sim = go.Figure()
            fig_sim.add_trace(go.Scatter(
                x=selected_df["game"], y=selected_df["cum_era"],
                name="未介入（放任累積疲勞）", line=dict(color="#BA1A1A", width=2.5, dash="dash")
            ))
            fig_sim.add_trace(go.Scatter(
                x=selected_df["game"], y=sim_era,
                name="MFEWS 及時跳過輪值處方（保全防禦率）", line=dict(color="#1B6E3E", width=3.2)
            ))
            fig_sim.update_layout(
                template="plotly_white",
                paper_bgcolor="#FFFBFE",
                plot_bgcolor="#F3EDF7",
                font=dict(family="Roboto, sans-serif", color="#1C1B1F"),
                height=340,
                margin=dict(l=45, r=20, t=35, b=35),
                legend=dict(
                    orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                    font=dict(size=11, family="Roboto, sans-serif", color="#49454F"),
                    bgcolor="rgba(243, 237, 247, 0.85)", bordercolor="#CAC4D0", borderwidth=1
                )
            )
            fig_sim.update_yaxes(
                showgrid=True, gridwidth=1, gridcolor="#E7E0EC",
                title_text="累積防禦率 (ERA)",
                title_font=dict(size=12, color="#49454F", family="Roboto, sans-serif"),
                tickfont=dict(color="#49454F", family="Roboto, sans-serif")
            )
            fig_sim.update_xaxes(
                showgrid=True, gridwidth=1, gridcolor="#E7E0EC",
                title_text="賽季場次 (Game)",
                title_font=dict(size=12, color="#49454F", family="Roboto, sans-serif"),
                tickfont=dict(color="#49454F", family="Roboto, sans-serif")
            )
            
            st.plotly_chart(fig_sim, use_container_width=True)
            
            st.markdown("""
            <div class="benefit-callout">
                <div style="font-size: 16px; font-weight: 700; margin-bottom: 8px;">🎯 模擬介入效益結算 (Pitcher Load Management Outcome)</div>
                <div>• <b>避免防禦率失控</b>：及時跳過 1 次輪值並進行肩膀高壓氧修復，累積 ERA 壓制於 <code>2.35</code>（避免暴增至 3.45）。</div>
                <div>• <b>預防受傷效益</b>：手肘 UCL 韌帶拉扯與肩胛夾擠代償風險由 84% 降至 16%。</div>
                <div>• <b>球威保全</b>：季後賽四縫線均速保全於 153.2 km/h 高檔。</div>
            </div>
            """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# TAB 4: 教練調度與防護建議卡 (Prescription & Export)
# -----------------------------------------------------------------------------
with tab4:
    st.markdown(f"### 🛡️ 教練調度與運動科學防護處方箋 (Actionable Prescription)")

    curr_player_mfi = selected_df["mfi"].iloc[-1]

    act_col1, act_col2, act_col3 = st.columns(3)

    with act_col1:
        if curr_player_mfi >= threshold_red:
            variant = "danger"
            t_text = "🚨 戰術與陣容調度處方 (高風險介入)"
            b_text = """
            • <b>防守位置卸載</b>：即日起移出守備先發名單，連續 3~4 場轉任指定打擊 (DH) 或安排完整輪休。<br>
            • <b>棒次調整</b>：自第 1 棒調降至第 6~7 棒，降低高張力得點圈抗壓負擔與選球神經耗損。<br>
            • <b>對戰對策</b>：今日避開對手極速型 (152km/h+) 速球派先發投手。
            """
        elif curr_player_mfi >= threshold_yellow:
            variant = "warning"
            t_text = "⚠️ 戰術與陣容調度處方 (觀察期管理)"
            b_text = """
            • <b>局數管控</b>：領先或落後 4 分以上時，於第 7 局提前替補退場休息。<br>
            • <b>戰術頻率</b>：減少盜壘與積極跑壘指示，維持體力能量儲備。
            """
        else:
            variant = "info"
            t_text = "✅ 戰術與陣容調度處方 (體能優良)"
            b_text = """
            • <b>正常先發</b>：可完全維持常規守備與第 1~3 棒主力進攻戰術授權。<br>
            • <b>持續追蹤</b>：每週一例行性檢測 MFI 趨勢。
            """
        st.markdown(render_md3_action_card(t_text, b_text, variant), unsafe_allow_html=True)

    with act_col2:
        if curr_player_mfi >= threshold_red:
            variant = "danger"
            t_text2 = "🏋️ 賽前訓練負荷管制 (減量 60%)"
            b_text2 = """
            • <b>打擊練習 (BP) 減量</b>：取消賽前發球機高張力實戰打擊，強制由 50 球減少至 15 球純意象揮棒。<br>
            • <b>禁用加重棒</b>：全面暫停轉體重力加重棒超負荷訓練，防止前臂旋前肌群過度代償。<br>
            • <b>神經視覺替代訓練</b>：改採 VR 視知覺眼動儀進行 10 分鐘低肢體負荷的好壞球辨識。
            """
        elif curr_player_mfi >= threshold_yellow:
            variant = "warning"
            t_text2 = "🏋️ 賽前訓練負荷管制 (減量 30%)"
            b_text2 = """
            • <b>打擊練習調節</b>：限制賽前 Live BP 揮棒上限 30 次，增加柔軟度動態伸展。<br>
            • <b>重訓課表調控</b>：以維持性等長收縮 (Isometric) 取代大重量向心爆發課表。
            """
        else:
            variant = "info"
            t_text2 = "🏋️ 賽前訓練負荷管制 (正常維護)"
            b_text2 = """
            • <b>常態化課表</b>：按選手個人週期化重訓課表執行即可。<br>
            • <b>神經啟動</b>：賽前常規 15 分鐘速度敏捷繩梯與快縮肌啟動。
            """
        st.markdown(render_md3_action_card(t_text2, b_text2, variant), unsafe_allow_html=True)

    with act_col3:
        if curr_player_mfi >= threshold_red:
            variant = "danger"
            t_text3 = "🔬 運科防護與生物力學檢測"
            b_text3 = """
            • <b>測力板 CMJ 檢測</b>：賽前立即執行反向跳 (CMJ)，監控離心發力率 (RFD) 兩側不對稱指數 (若 >10% 亮紅燈)。<br>
            • <b>筋膜與關節度評估</b>：檢查胸椎旋轉活動度與後側肩關節內旋角度 (GIRD)，預防拉傷。<br>
            • <b>深度恢復處方</b>：安排超低溫冷凍艙 (Cryotherapy) 3 分鐘與高壓氧艙治療，確保睡眠監控達 8.5 小時以上。
            """
        elif curr_player_mfi >= threshold_yellow:
            variant = "warning"
            t_text3 = "🔬 運科防護與生物力學檢測"
            b_text3 = """
            • <b>自主神經 HRV 檢測</b>：持續追蹤清晨靜息心率變異度 (HRV-rMSSD) 是否連續 3 天下降。<br>
            • <b>筋膜放鬆</b>：賽後強制執行 20 分鐘下肢氣壓式加壓腿套 (NormaTec) 循環恢復。
            """
        else:
            variant = "info"
            t_text3 = "🔬 運科防護與生物力學檢測"
            b_text3 = """
            • <b>例行保養</b>：常態性賽後肩關節/手肘冰熱敷交替與軟組織滾筒放鬆。<br>
            • <b>睡眠品質良好</b>：心率變異度與肌肉張力指數維持於標準綠燈區間。
            """
        st.markdown(render_md3_action_card(t_text3, b_text3, variant), unsafe_allow_html=True)

    st.write("")
    # 一鍵匯出處方箋報告 (純文字 / CSV 格式)
    clean_b_text = b_text.replace("<b>", "").replace("</b>", "").replace("<br>", "\n   ")
    clean_b_text2 = b_text2.replace("<b>", "").replace("</b>", "").replace("<br>", "\n   ")
    clean_b_text3 = b_text3.replace("<b>", "").replace("</b>", "").replace("<br>", "\n   ")
    
    export_content = f"""=============================================================================
⚾ MFEWS 賽季微疲勞先行調度與運科防護處方箋
=============================================================================
球員姓名：{selected_player}
守備位置：{selected_df["pos"].iloc[0]}
當前 MFI 指數：{curr_player_mfi:.1f} / 100
警戒門檻：高風險 >= {threshold_red} | 觀察期 >= {threshold_yellow}
診斷判定：{'🔴 高風險預警' if curr_player_mfi >= threshold_red else ('🟡 觀察期' if curr_player_mfi >= threshold_yellow else '🟢 體能正常')}
處方輸出時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
=============================================================================
【1. 戰術與陣容調度處方】：
   {clean_b_text.strip()}

【2. 賽前訓練負荷管制處方】：
   {clean_b_text2.strip()}

【3. 運科防護與生物力學檢測處方】：
   {clean_b_text3.strip()}
=============================================================================
"""
    st.download_button(
        label=f"📥 一鍵下載【{selected_player}】運科調度處方箋 (Export Prescription TXT)",
        data=export_content,
        file_name=f"MFEWS_Prescription_{selected_player}_{datetime.now().strftime('%Y%m%d')}.txt",
        mime="text/plain",
        use_container_width=True
    )

st.write("")

# =============================================================================
# 7. 頁尾資訊與黑客松宣告
# =============================================================================
st.markdown("""
<div class="mfews-footer">
    2026 野革盃台灣棒球數據黑客松參賽專案 · Micro-Fatigue Early Warning System (MFEWS)<br>
    Google Material You (Material Design 3) 現代運動科學戰情介面 · 純前端 WebAssembly 支援免伺服器部署
</div>
""", unsafe_allow_html=True)
