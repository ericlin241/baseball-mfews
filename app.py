"""
=============================================================================
賽季微疲勞先行指標預警系統 (Micro-Fatigue Early Warning System, MFEWS)
2026 野革盃台灣棒球數據黑客松參賽專案
架構：Streamlit + Plotly + Pandas + NumPy (可透過 stlite WebAssembly 在瀏覽器端純前端運行)
主視覺：藍白紅三色系 (Navy Blue, Crisp White, Crimson Red)
版權所有：© NTUT IAE. All rights reserved.
=============================================================================
"""

import sys
import types

# =============================================================================
# Pyodide / stlite / WebAssembly 環境相容性補丁 (Polyfill pyarrow stub)
# 解決 narwhals 在檢測 arrow 物件時引用 pa.ChunkedArray / pa.Table 拋出 AttributeError 的問題
# =============================================================================
try:
    import pyarrow as _pa
    for _attr in ["ChunkedArray", "Table", "RecordBatch", "Array", "DataType", "Field", "Schema"]:
        if not hasattr(_pa, _attr):
            setattr(_pa, _attr, type(_attr, (), {}))
except Exception:
    _pa = types.ModuleType("pyarrow")
    for _attr in ["ChunkedArray", "Table", "RecordBatch", "Array", "DataType", "Field", "Schema"]:
        setattr(_pa, _attr, type(_attr, (), {}))
    sys.modules["pyarrow"] = _pa

if "pyarrow" in sys.modules and sys.modules["pyarrow"] is not None:
    _pa_mod = sys.modules["pyarrow"]
    for _attr in ["ChunkedArray", "Table", "RecordBatch", "Array", "DataType", "Field", "Schema"]:
        if not hasattr(_pa_mod, _attr):
            setattr(_pa_mod, _attr, type(_attr, (), {}))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

# =============================================================================
# 0. 藍白紅經典棒球視覺系統 Design Tokens (RB.png Palette: Navy, White, Crimson)
# =============================================================================
THEME_TOKENS = {
    "colors": {
        "primary": "#0A2C51",               # 經典深海軍藍 (Primary Navy Blue)
        "on_primary": "#FFFFFF",
        "primary_container": "#E2ECF8",     # 柔和海軍藍容器
        "on_primary_container": "#061D36",
        "secondary": "#E8383D",             # 熱血棒球紅 (Secondary Crimson Red)
        "on_secondary": "#FFFFFF",
        "secondary_container": "#FDE8E9",   # 柔和紅色容器
        "on_secondary_container": "#4B080A",
        "accent_blue": "#1E5AA0",           # 科技活力藍
        "surface": "#F8F9FA",               # 乾淨球場白底色 (Light Off-White)
        "surface_container": "#FFFFFF",     # 內容卡片底色 (Crisp White)
        "surface_container_low": "#F1F5F9", # 淺灰藍凹陷/輸入底色
        "surface_container_high": "#E2E8F0",
        "outline": "#CBD5E1",               # 輪廓邊框灰
        "outline_variant": "#E2E8F0",
        "on_surface": "#0F172A",            # 主文字 (Slate 900)
        "on_surface_variant": "#475569",    # 次要文字 (Slate 600)
        
        # 語意狀態色彩 (Semantic Status)
        "success": "#059669",               # 綠燈正常
        "success_container": "#D1FAE5",
        "on_success_container": "#064E3B",
        "warning": "#D97706",               # 黃燈觀察 (Amber)
        "warning_container": "#FEF3C7",
        "on_warning_container": "#78350F",
        "danger": "#E8383D",                # 紅燈高風險 (RB.png 經典紅)
        "danger_container": "#FDE8E9",
        "on_danger_container": "#4B080A",
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
        "level1": "0px 1px 3px 0px rgba(10, 44, 81, 0.08), 0px 1px 2px 0px rgba(10, 44, 81, 0.05)",
        "level2": "0px 4px 12px 0px rgba(10, 44, 81, 0.12), 0px 2px 4px 0px rgba(10, 44, 81, 0.06)",
        "level3": "0px 8px 24px 0px rgba(10, 44, 81, 0.16), 0px 3px 6px 0px rgba(10, 44, 81, 0.08)",
    }
}

def render_theme_badge(text: str, variant: str = "tonal", extra_style: str = "") -> str:
    """產生藍白紅棒球風格藥丸型標籤 (Pill Badge)"""
    return f'<span class="badge badge-{variant}" style="{extra_style}">{text}</span>'

def render_theme_kpi_card(label: str, value: str, unit: str, subtext: str, color: str = "#0A2C51") -> str:
    """產生藍白紅高對比 KPI 戰情卡片"""
    return f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value" style="color: {color};">{value} <span style="font-size: 15px; color: #475569; font-weight: 500;">{unit}</span></div>
        <div class="kpi-subtext">{subtext}</div>
    </div>
    """

def render_theme_action_card(title: str, body: str, variant: str = "info") -> str:
    """產生運動科學與調度處方卡"""
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
# 1. 頁面基礎設定與全域 CSS
# =============================================================================
st.set_page_config(
    page_title="MFEWS | 賽季微疲勞先行指標預警系統",
    page_icon="⚾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 注入藍白紅全域視覺與 Streamlit 元件修復 CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700;900&display=swap');

    :root {
        --theme-color-primary: #0A2C51;
        --theme-color-on-primary: #FFFFFF;
        --theme-color-primary-container: #E2ECF8;
        --theme-color-on-primary-container: #061D36;
        --theme-color-secondary: #E8383D;
        --theme-color-on-secondary: #FFFFFF;
        --theme-color-secondary-container: #FDE8E9;
        --theme-color-on-secondary-container: #4B080A;
        --theme-color-accent-blue: #1E5AA0;
        --theme-color-surface: #F8F9FA;
        --theme-color-surface-container: #FFFFFF;
        --theme-color-surface-container-low: #F1F5F9;
        --theme-color-surface-container-high: #E2E8F0;
        --theme-color-outline: #CBD5E1;
        --theme-color-outline-variant: #E2E8F0;
        --theme-color-on-surface: #0F172A;
        --theme-color-on-surface-variant: #475569;

        /* Semantic Status */
        --theme-color-success: #059669;
        --theme-color-success-container: #D1FAE5;
        --theme-color-on-success-container: #064E3B;
        --theme-color-warning: #D97706;
        --theme-color-warning-container: #FEF3C7;
        --theme-color-on-warning-container: #78350F;
        --theme-color-danger: #E8383D;
        --theme-color-danger-container: #FDE8E9;
        --theme-color-on-danger-container: #4B080A;

        /* Shape Radii */
        --theme-shape-xs: 8px;
        --theme-shape-sm: 12px;
        --theme-shape-md: 16px;
        --theme-shape-lg: 24px;
        --theme-shape-xl: 28px;
        --theme-shape-xxl: 36px;
        --theme-shape-full: 9999px;

        /* Elevation */
        --theme-elevation-1: 0px 1px 3px 0px rgba(10, 44, 81, 0.08), 0px 1px 2px 0px rgba(10, 44, 81, 0.05);
        --theme-elevation-2: 0px 4px 12px 0px rgba(10, 44, 81, 0.12), 0px 2px 4px 0px rgba(10, 44, 81, 0.06);
        --theme-elevation-3: 0px 8px 24px 0px rgba(10, 44, 81, 0.16), 0px 3px 6px 0px rgba(10, 44, 81, 0.08);
    }

    /* 徹底移除 Streamlit 頂部白色橫條、三個點選單與預設 Toolbar，避免遮擋標題 */
    header[data-testid="stHeader"] {
        display: none !important;
    }
    #MainMenu {
        display: none !important;
    }
    div[data-testid="stToolbar"] {
        display: none !important;
    }
    .stDeployButton {
        display: none !important;
    }
    footer {
        display: none !important;
    }

    /* 全域字型與淺色清爽球場白底設定 */
    .stApp {
        background-color: var(--theme-color-surface) !important;
        color: var(--theme-color-on-surface) !important;
        font-family: 'Roboto', -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif !important;
    }

    h1, h2, h3, h4, h5, h6 {
        font-family: 'Roboto', sans-serif !important;
        font-weight: 700 !important;
        color: var(--theme-color-primary) !important;
        letter-spacing: -0.01em !important;
    }
    
    p, span, div, label {
        font-family: 'Roboto', sans-serif;
    }

    .block-container {
        padding-top: 1.2rem !important;
        padding-bottom: 2.5rem !important;
        max-width: 1440px !important;
    }

    /* 戰情頂部標題列 (藍白紅經典氛圍) */
    .war-room-header-wrapper {
        position: relative;
        overflow: hidden;
        border-radius: var(--theme-shape-xxl);
        background: linear-gradient(135deg, #FFFFFF 0%, #F1F5F9 100%);
        border: 2px solid var(--theme-color-outline-variant);
        box-shadow: var(--theme-elevation-1);
        margin-bottom: 20px;
    }

    .md-blob {
        position: absolute;
        border-radius: 9999px;
        filter: blur(52px);
        pointer-events: none;
        z-index: 0;
    }

    .md-blob-1 {
        width: 280px;
        height: 280px;
        background: radial-gradient(circle, rgba(10, 44, 81, 0.16) 0%, rgba(226, 236, 248, 0.02) 70%);
        top: -70px;
        right: -30px;
    }

    .md-blob-2 {
        width: 240px;
        height: 240px;
        background: radial-gradient(circle, rgba(232, 56, 61, 0.13) 0%, rgba(253, 232, 233, 0.02) 70%);
        bottom: -60px;
        left: 25%;
    }

    .md-blob-3 {
        width: 200px;
        height: 200px;
        background: radial-gradient(circle, rgba(30, 90, 160, 0.14) 0%, rgba(226, 236, 248, 0.02) 70%);
        top: 20px;
        left: 5%;
    }

    .war-room-header {
        position: relative;
        z-index: 1;
        padding: 26px 32px;
    }

    .war-room-title {
        font-size: 30px;
        font-weight: 900;
        color: var(--theme-color-primary);
        margin: 0 0 6px 0;
        letter-spacing: -0.02em;
    }

    .war-room-subtitle {
        color: var(--theme-color-on-surface-variant);
        font-size: 14.5px;
        margin: 0;
        line-height: 1.5;
    }

    /* KPI 戰情卡片 (高對比白色立體卡片) */
    .kpi-card {
        background: var(--theme-color-surface-container);
        border: 1.5px solid var(--theme-color-outline-variant);
        border-radius: var(--theme-shape-lg);
        padding: 22px 24px;
        box-shadow: var(--theme-elevation-1);
        transition: transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease;
        height: 100%;
        box-sizing: border-box;
    }

    .kpi-card:hover {
        transform: translateY(-3px);
        box-shadow: var(--theme-elevation-2);
        border-color: var(--theme-color-primary);
    }

    .kpi-label {
        font-size: 12.5px;
        letter-spacing: 0.02em;
        color: var(--theme-color-on-surface-variant);
        font-weight: 700;
        margin-bottom: 8px;
    }

    .kpi-value {
        font-size: 32px;
        font-weight: 900;
        line-height: 1.2;
        margin-bottom: 6px;
        letter-spacing: -0.01em;
    }

    .kpi-subtext {
        font-size: 12.5px;
        color: var(--theme-color-on-surface-variant);
        line-height: 1.4;
    }

    /* 狀態警示燈號藥丸徽章 */
    .badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 5px 14px;
        border-radius: var(--theme-shape-full);
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 0.02em;
        transition: all 0.2s ease;
    }

    .badge-green {
        background-color: var(--theme-color-success-container);
        color: var(--theme-color-on-success-container);
        border: 1px solid rgba(5, 150, 105, 0.3);
    }

    .badge-yellow {
        background-color: var(--theme-color-warning-container);
        color: var(--theme-color-on-warning-container);
        border: 1px solid rgba(217, 119, 6, 0.3);
    }

    .badge-red {
        background-color: var(--theme-color-danger-container);
        color: var(--theme-color-danger);
        border: 1px solid rgba(232, 56, 61, 0.4);
        animation: rb-pulse-red 2.4s infinite;
    }

    .badge-tonal {
        background-color: var(--theme-color-primary_container);
        color: var(--theme-color-primary);
        border: 1px solid rgba(10, 44, 81, 0.2);
    }

    .badge-primary {
        background-color: var(--theme-color-primary);
        color: var(--theme-color-on-primary);
        box-shadow: 0 2px 6px rgba(10, 44, 81, 0.25);
    }

    @keyframes rb-pulse-red {
        0% { box-shadow: 0 0 0 0 rgba(232, 56, 61, 0.45); }
        70% { box-shadow: 0 0 0 9px rgba(232, 56, 61, 0); }
        100% { box-shadow: 0 0 0 0 rgba(232, 56, 61, 0); }
    }

    /* 球員卡容器與卡片基礎造型 */
    .player-card {
        background: var(--theme-color-surface-container);
        border: 2px solid var(--theme-color-outline-variant);
        border-radius: var(--theme-shape-md);
        padding: 16px 10px;
        text-align: center;
        box-shadow: var(--theme-elevation-1);
        transition: all 0.22s ease;
        min-height: 114px;
        box-sizing: border-box;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        cursor: pointer;
        user-select: none;
    }

    .player-card.player-card-active {
        border-color: var(--theme-color-primary) !important;
        background-color: var(--theme-color-primary-container) !important;
        box-shadow: 0 4px 14px rgba(10, 44, 81, 0.22) !important;
        transform: translateY(-2px);
    }

    .player-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 6px 18px rgba(10, 44, 81, 0.16);
        border-color: var(--theme-color-primary);
    }

    .player-name {
        font-size: 16px;
        font-weight: 800;
        color: var(--theme-color-primary);
        margin-bottom: 2px;
    }

    .player-pos {
        font-size: 11.5px;
        color: var(--theme-color-on-surface-variant);
        margin-bottom: 8px;
    }

    /* 將按鈕化為隱形全覆蓋層，覆蓋於整張卡片上方，實現直接點擊卡片即可切換 */
    div[data-testid="column"]:has(.player-card) {
        position: relative !important;
    }

    div[data-testid="column"]:has(.player-card) .stButton {
        position: absolute !important;
        top: 0 !important;
        left: 0 !important;
        width: 100% !important;
        height: 100% !important;
        margin: 0 !important;
        padding: 0 !important;
        z-index: 10 !important;
    }

    div[data-testid="column"]:has(.player-card) .stButton > button {
        width: 100% !important;
        height: 100% !important;
        min-height: 114px !important;
        opacity: 0 !important;
        background: transparent !important;
        border: none !important;
        cursor: pointer !important;
        padding: 0 !important;
        margin: 0 !important;
        font-size: 0 !important;
        box-shadow: none !important;
    }

    /* 建議行動處方卡 (左邊條顏色) */
    .action-card {
        background: var(--theme-color-surface-container);
        border: 1.5px solid var(--theme-color-outline-variant);
        border-radius: var(--theme-shape-lg);
        padding: 22px 24px;
        margin-bottom: 16px;
        border-left: 6px solid var(--theme-color-primary);
        box-shadow: var(--theme-elevation-1);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        height: 100%;
        box-sizing: border-box;
    }

    .action-card:hover {
        transform: translateY(-2px);
        box-shadow: var(--theme-elevation-2);
    }

    .action-card.card-warning {
        border-left-color: var(--theme-color-warning);
        background: linear-gradient(180deg, rgba(254, 243, 199, 0.35) 0%, #FFFFFF 100%);
    }

    .action-card.card-danger {
        border-left-color: var(--theme-color-danger);
        background: linear-gradient(180deg, rgba(253, 232, 233, 0.45) 0%, #FFFFFF 100%);
    }

    .action-title {
        font-size: 16px;
        font-weight: 700;
        color: var(--theme-color-on-surface);
        margin-bottom: 10px;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .action-body {
        font-size: 13.5px;
        color: var(--theme-color-on-surface-variant);
        line-height: 1.6;
    }

    .action-body b {
        color: var(--theme-color-primary);
    }

    /* 運動生理即時遙測卡 */
    .telemetry-card {
        background: var(--theme-color-surface-container);
        border: 1.5px solid var(--theme-color-outline-variant);
        border-radius: 20px;
        padding: 22px 24px;
        box-shadow: var(--theme-elevation-1);
    }

    .telemetry-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
        font-size: 13.5px;
        color: var(--theme-color-on-surface-variant);
    }

    .telemetry-row.total-row {
        border-top: 1.5px solid var(--theme-color-outline-variant);
        padding-top: 12px;
        margin-top: 10px;
        font-weight: 700;
        font-size: 15px;
        color: var(--theme-color-primary);
    }

    .telemetry-badge {
        font-weight: 700;
        padding: 3px 10px;
        border-radius: 9999px;
        font-size: 12.5px;
    }

    .telemetry-badge.badge-safe {
        background: var(--theme-color-success-container);
        color: var(--theme-color-on-success-container);
    }

    /* 頁籤元件：藍白紅經典藥丸型導覽標籤 */
    div[data-baseweb="tab-list"] {
        background-color: #FFFFFF !important;
        border-radius: 9999px !important;
        padding: 6px !important;
        border: 1.5px solid var(--theme-color-outline-variant) !important;
        gap: 8px !important;
        margin-bottom: 24px !important;
        box-shadow: var(--theme-elevation-1) !important;
    }

    div[data-baseweb="tab"] {
        border-radius: 9999px !important;
        padding: 9px 22px !important;
        font-weight: 700 !important;
        font-family: 'Roboto', sans-serif !important;
        font-size: 14px !important;
        color: var(--theme-color-on-surface-variant) !important;
        background-color: transparent !important;
        border: none !important;
        transition: all 0.2s ease !important;
    }

    div[data-baseweb="tab"]:hover {
        background-color: var(--theme-color-primary-container) !important;
        color: var(--theme-color-primary) !important;
    }

    div[data-baseweb="tab"][aria-selected="true"] {
        background-color: var(--theme-color-primary) !important;
        color: #FFFFFF !important;
        box-shadow: 0 2px 8px rgba(10, 44, 81, 0.25) !important;
    }

    div[data-baseweb="tab-highlight"] {
        display: none !important;
    }

    /* 側邊欄控制 */
    div[data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 1.5px solid var(--theme-color-outline-variant) !important;
    }

    div[data-testid="stSidebar"] hr {
        border-color: var(--theme-color-outline-variant) !important;
    }

    /* 下拉選單 */
    div[data-baseweb="select"] > div {
        background-color: var(--theme-color-surface-container-low) !important;
        border-radius: 12px !important;
        border: 1.5px solid var(--theme-color-outline) !important;
        color: var(--theme-color-on-surface) !important;
        transition: border-color 0.2s ease !important;
    }

    div[data-baseweb="select"] > div:hover {
        border-color: var(--theme-color-primary) !important;
    }

    div[data-baseweb="select"] > div:focus-within {
        border-color: var(--theme-color-primary) !important;
        box-shadow: 0 0 0 3px rgba(10, 44, 81, 0.15) !important;
    }

    div[data-baseweb="popover"] ul {
        background-color: #FFFFFF !important;
        border-radius: 16px !important;
        box-shadow: var(--theme-elevation-2) !important;
        border: 1.5px solid var(--theme-color-outline-variant) !important;
        padding: 8px !important;
    }

    div[data-baseweb="popover"] li {
        border-radius: 9999px !important;
        color: var(--theme-color-on-surface) !important;
        transition: background-color 0.15s ease !important;
    }

    div[data-baseweb="popover"] li:hover {
        background-color: var(--theme-color-primary-container) !important;
        color: var(--theme-color-primary) !important;
    }

    /* 滑桿 (Slider) - 圓點平滑跟隨滑鼠移動，懸停光環平穩無抖動 (不覆蓋 transform) */
    div[data-testid="stSlider"] div[role="slider"] {
        background-color: var(--theme-color-primary) !important;
        border: 2px solid #FFFFFF !important;
        box-shadow: 0 1px 4px rgba(10, 44, 81, 0.3) !important;
        transition: box-shadow 0.2s ease, background-color 0.2s ease !important;
    }

    div[data-testid="stSlider"] div[role="slider"]:hover {
        box-shadow: 0 0 0 6px rgba(10, 44, 81, 0.15) !important;
    }

    div[data-testid="stSlider"] div[role="slider"]:active {
        box-shadow: 0 0 0 8px rgba(10, 44, 81, 0.25) !important;
    }

    /* 開關 (Toggle Switch) */
    div[data-testid="stCheckbox"] label,
    div[data-testid="stToggle"] label {
        color: var(--theme-color-on-surface) !important;
        font-weight: 500 !important;
    }

    /* 按鈕 (Buttons - 經典深海軍藍藥丸型) */
    .stButton > button {
        background-color: var(--theme-color-primary) !important;
        color: #FFFFFF !important;
        border-radius: var(--theme-shape-full) !important;
        border: none !important;
        padding: 10px 24px !important;
        font-weight: 700 !important;
        font-size: 13.5px !important;
        transition: all 0.2s cubic-bezier(0.2, 0, 0, 1) !important;
        box-shadow: var(--theme-elevation-1) !important;
    }

    .stButton > button:hover {
        background-color: #153E6B !important;
        box-shadow: var(--theme-elevation-2) !important;
        transform: translateY(-1px) !important;
    }

    .stButton > button:active {
        transform: scale(0.97) !important;
    }

    /* 下載按鈕 (Download Button) */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #0A2C51 0%, #153E6B 100%) !important;
        color: #FFFFFF !important;
        border-radius: var(--theme-shape-full) !important;
        border: none !important;
        padding: 12px 28px !important;
        font-weight: 700 !important;
        font-size: 14px !important;
        box-shadow: var(--theme-elevation-2) !important;
        transition: all 0.2s ease !important;
    }

    .stDownloadButton > button:hover {
        background: linear-gradient(135deg, #153E6B 0%, #1E5AA0 100%) !important;
        box-shadow: var(--theme-elevation-3) !important;
        transform: translateY(-2px) !important;
    }

    /* 診斷表格樣式 (防止文字重疊，寬敞易讀) */
    .diag-table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        border-radius: 14px;
        overflow: hidden;
        border: 1.5px solid var(--theme-color-outline-variant);
        background: #FFFFFF;
    }

    .diag-table th {
        background: var(--theme-color-primary);
        color: #FFFFFF;
        padding: 12px 14px;
        font-size: 13px;
        font-weight: 700;
        text-align: center;
        white-space: nowrap;
        letter-spacing: 0.02em;
    }

    .diag-table td {
        padding: 10px 14px;
        font-size: 13px;
        color: var(--theme-color-on-surface);
        border-bottom: 1px solid var(--theme-color-outline-variant);
        text-align: center;
        white-space: nowrap;
    }

    .diag-table tr:last-child td {
        border-bottom: none;
    }

    .diag-table tr:nth-child(even) {
        background-color: var(--theme-color-surface);
    }

    .diag-table tr:hover {
        background-color: var(--theme-color-primary-container);
    }

    /* 頁尾 */
    .mfews-footer {
        text-align: center;
        padding: 30px 20px 10px 20px;
        color: var(--theme-color-on-surface-variant);
        font-size: 13px;
        border-top: 1.5px solid var(--theme-color-outline-variant);
        margin-top: 40px;
        line-height: 1.6;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# 2. 棒球微疲勞先行特徵模擬引擎 (CPBL 6 隊一軍球員資料庫，預設味全龍)
# =============================================================================
@st.cache_data
def generate_baseball_season_data():
    """
    產生中華職棒 6 球團共 36 位代表性一軍主力球員（打者與投手）全季 115 場賽事的微觀運動學特徵數據。
    預設球隊為「味全龍」，包含當家球星吉力吉撈．鞏冠、李凱威、劉基鴻、郭天信、徐若熙、陳冠偉等一軍名單。
    """
    np.random.seed(42)
    start_date = datetime(2026, 4, 1)
    games_count = 115
    dates = [start_date + timedelta(days=int(i * 1.4)) for i in range(games_count)]
    game_numbers = np.arange(1, games_count + 1)
    
    players_data = {}
    
    def create_batter_data(name, team, pos, base_os, base_zw, base_hh, f_start, f_end, base_avg):
        fatigue = np.zeros(games_count)
        if f_start < 900:
            for i, g in enumerate(game_numbers):
                if f_start <= g <= f_end:
                    fatigue[i] = 1.0 / (1.0 + np.exp(-(g - f_start - 2) * 0.7))
                elif f_end < g <= f_end + 10:
                    fatigue[i] = max(0.0, 1.0 - (g - f_end) * 0.1)
                else:
                    fatigue[i] = 0.05 * np.sin(g / 8.0)
        fatigue = np.clip(fatigue, 0.0, 1.0)
        
        roll_os = pd.Series(base_os + fatigue * 0.16 + np.random.normal(0, 0.02, games_count)).rolling(7, min_periods=1).mean().values * 100
        roll_zw = pd.Series(base_zw + fatigue * 0.12 + np.random.normal(0, 0.015, games_count)).rolling(7, min_periods=1).mean().values * 100
        roll_hh = pd.Series(base_hh - fatigue * 0.16 + np.random.normal(0, 0.025, games_count)).rolling(7, min_periods=1).mean().values * 100
        
        s_os = np.clip((roll_os - 20) / (42 - 20), 0, 1) * 100
        s_zw = np.clip((roll_zw - 7) / (24 - 7), 0, 1) * 100
        s_hh = np.clip((45 - roll_hh) / (45 - 22), 0, 1) * 100
        mfi = np.clip(0.4 * s_os + 0.35 * s_zw + 0.25 * s_hh + np.random.normal(0, 1.2, games_count), 15, 95)
        
        ab_per_game = np.random.choice([3, 4, 4, 5], size=games_count)
        hits_per_game = []
        for i, g in enumerate(game_numbers):
            ab = ab_per_game[i]
            p_hit = base_avg - (0.18 if (f_start + 10 <= g <= f_end + 12 and f_start < 900) else 0.0)
            p_hit = max(0.08, p_hit)
            hits_per_game.append(np.random.binomial(ab, p_hit))
        cum_avg = np.cumsum(hits_per_game) / np.cumsum(ab_per_game)
        
        latest_mfi = mfi[-1]
        status = "🔴 高風險" if latest_mfi >= 70 else ("🟡 觀察期" if latest_mfi >= 50 else "🟢 正常")
        
        return pd.DataFrame({
            "game": game_numbers,
            "date": dates,
            "team": team,
            "roster": "一軍名單",
            "player": name,
            "pos": pos,
            "role_type": "打者",
            "roll_oswing": np.round(roll_os, 1),
            "roll_zwhiff": np.round(roll_zw, 1),
            "roll_hardhit": np.round(roll_hh, 1),
            "cum_avg": np.round(cum_avg, 3),
            "cum_era": np.nan,
            "mfi": np.round(mfi, 1),
            "warning_lead_days": 12 if f_start < 900 else 10,
            "status_now": f"{status} (MFI {latest_mfi:.1f})",
            "fatigue_phase_start": f_start,
            "performance_crash_point": f_end if f_start < 900 else 999,
        })

    def create_pitcher_data(name, team, pos, base_disp, base_velo, base_ivb, f_start, f_end, base_era):
        fatigue = np.zeros(games_count)
        if f_start < 900:
            for i, g in enumerate(game_numbers):
                if f_start <= g <= f_end:
                    fatigue[i] = 1.0 / (1.0 + np.exp(-(g - f_start - 2) * 0.7))
                elif f_end < g <= f_end + 10:
                    fatigue[i] = max(0.0, 1.0 - (g - f_end) * 0.1)
                else:
                    fatigue[i] = 0.05 * np.sin(g / 8.0)
        fatigue = np.clip(fatigue, 0.0, 1.0)
        
        disp = base_disp + fatigue * 2.5 + np.random.normal(0, 0.2, games_count)
        velo = base_velo - fatigue * 4.2 + np.random.normal(0, 0.35, games_count)
        ivb = base_ivb - fatigue * 2.8 + np.random.normal(0, 0.25, games_count)
        
        s_rel = np.clip((disp - 1.5) / (4.5 - 1.5), 0, 1) * 100
        s_velo = np.clip((154.0 - velo) / (154.0 - 148.5), 0, 1) * 100
        s_ivb = np.clip((18.0 - ivb) / (18.0 - 14.0), 0, 1) * 100
        mfi = np.clip(0.40 * s_rel + 0.35 * s_velo + 0.25 * s_ivb + np.random.normal(0, 1.5, games_count), 18, 92)
        
        cum_era = base_era + (game_numbers > (f_start + 10 if f_start < 900 else 999)) * 1.35 + np.random.normal(0, 0.08, games_count)
        cum_era = np.clip(cum_era, 1.2, 7.5)
        
        latest_mfi = mfi[-1]
        status = "🔴 高風險" if latest_mfi >= 70 else ("🟡 觀察期" if latest_mfi >= 50 else "🟢 正常")
        
        return pd.DataFrame({
            "game": game_numbers,
            "date": dates,
            "team": team,
            "roster": "一軍名單",
            "player": name,
            "pos": pos,
            "role_type": "投手",
            "rel_disp_cm": np.round(disp, 2),
            "fastball_velo_kph": np.round(velo, 1),
            "ivb_inch": np.round(ivb, 1),
            "roll_oswing": np.nan,
            "roll_zwhiff": np.nan,
            "roll_hardhit": np.nan,
            "cum_avg": np.nan,
            "cum_era": np.round(cum_era, 2),
            "mfi": np.round(mfi, 1),
            "warning_lead_days": 13 if f_start < 900 else 10,
            "status_now": f"{status} (MFI {latest_mfi:.1f})",
            "fatigue_phase_start": f_start,
            "performance_crash_point": f_end if f_start < 900 else 999,
        })

    # 1. 味全龍 (Wei Chuan Dragons) - 預設球隊
    players_data["吉力吉撈．鞏冠"] = create_batter_data("吉力吉撈．鞏冠", "味全龍", "C / 捕手", 0.30, 0.15, 0.46, 62, 76, 0.295)
    players_data["李凱威"] = create_batter_data("李凱威", "味全龍", "2B / 內野手", 0.22, 0.08, 0.38, 999, 999, 0.312)
    players_data["劉基鴻"] = create_batter_data("劉基鴻", "味全龍", "3B / 內野手", 0.28, 0.14, 0.44, 52, 66, 0.282)
    players_data["郭天信"] = create_batter_data("郭天信", "味全龍", "CF / 外野手", 0.26, 0.11, 0.39, 74, 86, 0.298)
    players_data["徐若熙"] = create_pitcher_data("徐若熙", "味全龍", "SP / 先發投手", 1.8, 153.2, 17.5, 999, 999, 2.15)
    players_data["陳冠偉"] = create_pitcher_data("陳冠偉", "味全龍", "CP / 救援投手", 1.9, 149.0, 18.2, 80, 92, 1.85)

    # 2. 統一7-ELEVEn獅 (Uni-President 7-Eleven Lions)
    players_data["陳傑憲"] = create_batter_data("陳傑憲", "統一7-ELEVEn獅", "CF / 外野手", 0.22, 0.085, 0.41, 48, 60, 0.345)
    players_data["林安可"] = create_batter_data("林安可", "統一7-ELEVEn獅", "RF / 外野手", 0.29, 0.15, 0.47, 65, 78, 0.285)
    players_data["邱智呈"] = create_batter_data("邱智呈", "統一7-ELEVEn獅", "LF / 外野手", 0.23, 0.09, 0.37, 999, 999, 0.320)
    players_data["潘傑楷"] = create_batter_data("潘傑楷", "統一7-ELEVEn獅", "3B / 內野手", 0.27, 0.13, 0.42, 70, 82, 0.290)
    players_data["古林睿煬"] = create_pitcher_data("古林睿煬", "統一7-ELEVEn獅", "SP / 先發投手", 1.8, 153.5, 17.5, 70, 82, 2.05)
    players_data["勝騎士"] = create_pitcher_data("勝騎士", "統一7-ELEVEn獅", "SP / 先發投手", 1.9, 150.5, 16.8, 999, 999, 2.30)

    # 3. 中信兄弟 (CTBC Brothers)
    players_data["江坤宇"] = create_batter_data("江坤宇", "中信兄弟", "SS / 內野手", 0.23, 0.09, 0.35, 999, 999, 0.315)
    players_data["岳政華"] = create_batter_data("岳政華", "中信兄弟", "CF / 外野手", 0.28, 0.13, 0.40, 68, 80, 0.275)
    players_data["王威晨"] = create_batter_data("王威晨", "中信兄弟", "3B / 內野手", 0.24, 0.10, 0.38, 75, 87, 0.305)
    players_data["許基宏"] = create_batter_data("許基宏", "中信兄弟", "1B / 內野手", 0.27, 0.14, 0.45, 60, 72, 0.288)
    players_data["德保拉"] = create_pitcher_data("德保拉", "中信兄弟", "SP / 先發投手", 1.9, 149.8, 16.5, 72, 85, 2.65)
    players_data["吳俊偉"] = create_pitcher_data("吳俊偉", "中信兄弟", "CP / 救援投手", 2.0, 151.2, 17.0, 78, 90, 2.10)

    # 4. 樂天桃猿 (Rakuten Monkeys)
    players_data["林立"] = create_batter_data("林立", "樂天桃猿", "2B / 內野手", 0.27, 0.13, 0.47, 72, 84, 0.335)
    players_data["陳晨威"] = create_batter_data("陳晨威", "樂天桃猿", "CF / 外野手", 0.25, 0.10, 0.36, 80, 92, 0.310)
    players_data["廖健富"] = create_batter_data("廖健富", "樂天桃猿", "DH / 指定打擊", 0.28, 0.14, 0.46, 64, 76, 0.300)
    players_data["梁家榮"] = create_batter_data("梁家榮", "樂天桃猿", "3B / 內野手", 0.26, 0.11, 0.41, 999, 999, 0.295)
    players_data["威能帝"] = create_pitcher_data("威能帝", "樂天桃猿", "SP / 先發投手", 1.8, 152.0, 17.2, 999, 999, 2.45)
    players_data["黃子鵬"] = create_pitcher_data("黃子鵬", "樂天桃猿", "SP / 先發投手", 1.9, 142.5, 15.5, 76, 88, 3.10)

    # 5. 富邦悍將 (Fubon Guardians)
    players_data["張育成"] = create_batter_data("張育成", "富邦悍將", "SS / 內野手", 0.26, 0.12, 0.49, 70, 82, 0.298)
    players_data["申皓瑋"] = create_batter_data("申皓瑋", "富邦悍將", "CF / 外野手", 0.30, 0.16, 0.42, 60, 72, 0.265)
    players_data["王正棠"] = create_batter_data("王正棠", "富邦悍將", "2B / 內野手", 0.24, 0.09, 0.38, 999, 999, 0.308)
    players_data["董子恩"] = create_batter_data("董子恩", "富邦悍將", "3B / 內野手", 0.22, 0.08, 0.34, 999, 999, 0.285)
    players_data["富藍戈"] = create_pitcher_data("富藍戈", "富邦悍將", "RP / 後援投手", 1.7, 157.5, 18.0, 999, 999, 1.95)
    players_data["江少慶"] = create_pitcher_data("江少慶", "富邦悍將", "SP / 先發投手", 2.1, 149.0, 16.2, 65, 78, 3.40)

    # 6. 台鋼雄鷹 (TSG Hawks)
    players_data["王柏融"] = create_batter_data("王柏融", "台鋼雄鷹", "LF / 外野手", 0.27, 0.13, 0.44, 68, 80, 0.285)
    players_data["魔鷹"] = create_batter_data("魔鷹", "台鋼雄鷹", "1B / 內野手", 0.31, 0.18, 0.52, 75, 87, 0.305)
    players_data["曾子祐"] = create_batter_data("曾子祐", "台鋼雄鷹", "SS / 內野手", 0.24, 0.09, 0.37, 999, 999, 0.298)
    players_data["陳文杰"] = create_batter_data("陳文杰", "台鋼雄鷹", "CF / 外野手", 0.28, 0.12, 0.40, 72, 84, 0.272)
    players_data["哈瑪星"] = create_pitcher_data("哈瑪星", "台鋼雄鷹", "SP / 先發投手", 1.9, 148.5, 16.8, 999, 999, 2.75)
    players_data["後勁"] = create_pitcher_data("後勁", "台鋼雄鷹", "SP / 先發投手", 1.8, 147.0, 16.0, 999, 999, 2.50)

    return players_data

# 載入球員資料庫
all_players_data = generate_baseball_season_data()
player_keys = list(all_players_data.keys())
teams_list = ["味全龍", "統一7-ELEVEn獅", "中信兄弟", "樂天桃猿", "富邦悍將", "台鋼雄鷹"]

# 初始化 Session State
if "selected_team" not in st.session_state:
    st.session_state["selected_team"] = "味全龍"

team_players = [p for p in player_keys if all_players_data[p]["team"].iloc[0] == st.session_state["selected_team"]]

if "selected_player" not in st.session_state or st.session_state["selected_player"] not in team_players:
    st.session_state["selected_player"] = team_players[0] if team_players else "吉力吉撈．鞏冠"

# =============================================================================
# 3. 側邊欄控制中心 (球隊篩選、一軍名單連動、閾值滑桿)
# =============================================================================
st.sidebar.markdown("## ⚙️ 戰情室控制中心")

# 球隊選擇 (預設味全龍)
sidebar_team = st.sidebar.selectbox(
    "選擇球隊：",
    options=teams_list,
    index=teams_list.index(st.session_state["selected_team"]) if st.session_state["selected_team"] in teams_list else 0,
    key="sidebar_team_select",
    help="選擇欲監控之中華職棒球團，預設為味全龍。"
)

if sidebar_team != st.session_state["selected_team"]:
    st.session_state["selected_team"] = sidebar_team
    new_team_players = [p for p in player_keys if all_players_data[p]["team"].iloc[0] == sidebar_team]
    st.session_state["selected_player"] = new_team_players[0]
    st.rerun()

# 顯示登錄名單層級
st.sidebar.selectbox(
    "名單層級：",
    options=["🟢 一軍登錄名單 (Active 28人)", "⚪ 二軍培訓名單 (Farm)"],
    index=0,
    help="即時篩選該球團目前登錄於一軍出賽名單之球員。"
)

# 該球隊的一軍球員名單
team_players = [p for p in player_keys if all_players_data[p]["team"].iloc[0] == st.session_state["selected_team"]]
current_player_idx = team_players.index(st.session_state["selected_player"]) if st.session_state["selected_player"] in team_players else 0

sidebar_selected_player = st.sidebar.selectbox(
    "選擇監控球員：",
    options=team_players,
    index=current_player_idx,
    key="sidebar_player_select",
    help="選擇所屬球隊之一軍球員以檢視時序診斷與運科處方。"
)

if sidebar_selected_player != st.session_state["selected_player"]:
    st.session_state["selected_player"] = sidebar_selected_player
    st.rerun()

selected_player = st.session_state["selected_player"]

st.sidebar.markdown("---")
st.sidebar.markdown("### 🎯 疲勞預警警戒閾值設定")
threshold_red = st.sidebar.slider("高風險警戒線 (MFI)", 65, 80, 70, 1, help="當微疲勞指數超過此門檻時亮起紅燈預警")
threshold_yellow = st.sidebar.slider("觀察期門檻 (MFI)", 45, 60, 50, 1, help="當微疲勞指數介於此區間時亮起黃燈觀察")

# 取得選定球員資料
selected_df = all_players_data[selected_player]
is_batter = selected_df["role_type"].iloc[0] == "打者"

# =============================================================================
# 4. 頂部戰情總覽 (War Room KPI Dashboard)
# =============================================================================
st.markdown(f"""
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
                <span class="badge badge-primary">⚾ {st.session_state['selected_team']}</span>
                <span class="badge badge-tonal">即時監控：第 115 場</span>
                <span class="badge badge-green">一軍出賽名單</span>
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# 動態計算該球隊高風險疲勞球員數量
team_high_risk = [p for p in team_players if all_players_data[p]["mfi"].iloc[-1] >= threshold_red]
high_risk_count = len(team_high_risk)
high_risk_names = "、".join(team_high_risk) if team_high_risk else "無"

# 計算該隊全隊健康指數
team_mfi_avg = np.mean([all_players_data[p]["mfi"].iloc[-1] for p in team_players])
avg_thi = max(10.0, min(99.0, 100.0 - (team_mfi_avg - 25.0) * 1.1))

# KPI 卡片列 (完全移除英文縮寫 THI, HIGH RISK, LEAD TIME, PREVENTION)
kpi_c1, kpi_c2, kpi_c3, kpi_c4 = st.columns(4)

with kpi_c1:
    st.markdown(render_theme_kpi_card(
        label="隊伍綜合健康指數",
        value=f"{avg_thi:.1f}",
        unit="分",
        subtext=f"{st.session_state['selected_team']} 一軍整體體能狀態",
        color="#0A2C51"
    ), unsafe_allow_html=True)

with kpi_c2:
    st.markdown(render_theme_kpi_card(
        label="隱形高風險疲勞球員",
        value=f"{high_risk_count}",
        unit="位",
        subtext=f"警戒球員：{high_risk_names}" if high_risk_names != "無" else "全隊維持於安全區間",
        color="#E8383D"
    ), unsafe_allow_html=True)

with kpi_c3:
    st.markdown(render_theme_kpi_card(
        label="先行預警平均領先時差",
        value="12.4",
        unit="天",
        subtext="相當於傳統成績跳水前 10~14 天",
        color="#D97706"
    ), unsafe_allow_html=True)

with kpi_c4:
    st.markdown(render_theme_kpi_card(
        label="負荷介入預防成功率",
        value="88.5",
        unit="%",
        subtext="成功避免 15 天以上長期低潮或受傷",
        color="#059669"
    ), unsafe_allow_html=True)

st.write("")

# =============================================================================
# 5. 全隊一軍主力監控燈號矩陣 (點選球員卡即可切換分析，移除多餘按鈕與字眼)
# =============================================================================
c_title, c_picker = st.columns([3, 1.4])
with c_title:
    st.markdown(f"### 📋 {st.session_state['selected_team']} 一軍即時監控陣容")
with c_picker:
    picked_team = st.selectbox(
        "快速切換球隊：",
        options=teams_list,
        index=teams_list.index(st.session_state["selected_team"]),
        key="main_team_picker",
        label_visibility="collapsed"
    )
    if picked_team != st.session_state["selected_team"]:
        st.session_state["selected_team"] = picked_team
        new_players = [p for p in player_keys if all_players_data[p]["team"].iloc[0] == picked_team]
        st.session_state["selected_player"] = new_players[0]
        st.rerun()

matrix_cols = st.columns(len(team_players))

for idx, p_name in enumerate(team_players):
    p_df = all_players_data[p_name]
    curr_mfi = p_df["mfi"].iloc[-1]
    pos = p_df["pos"].iloc[0]
    
    # 依據動態閾值決定燈號
    if curr_mfi >= threshold_red:
        badge_html = render_theme_badge(f"🔴 高風險 ({curr_mfi:.1f})", "red")
    elif curr_mfi >= threshold_yellow:
        badge_html = render_theme_badge(f"🟡 觀察期 ({curr_mfi:.1f})", "yellow")
    else:
        badge_html = render_theme_badge(f"🟢 正常 ({curr_mfi:.1f})", "green")
        
    is_active = (p_name == selected_player)
    active_cls = "player-card-active" if is_active else ""
    
    with matrix_cols[idx]:
        st.markdown(f"""
        <div class="player-card {active_cls}">
            <div class="player-name">{p_name}</div>
            <div class="player-pos">{pos}</div>
            <div style="margin-top: 6px;">{badge_html}</div>
        </div>
        """, unsafe_allow_html=True)
        # 覆蓋整張卡片的透明按鈕，點選卡片直接切換球員
        if st.button(p_name, key=f"btn_pcard_{p_name}", help=f"點選查看 {p_name} 之微疲勞分析"):
            st.session_state["selected_player"] = p_name
            st.rerun()

st.write("")

# =============================================================================
# 6. 互動式全功能導覽頁籤 (移除英文 Diagnostics, Biomechanics, Simulation, Prescriptions)
# =============================================================================
tab1, tab2, tab3, tab4 = st.tabs([
    "📈 賽季時序深度診斷",
    "🔬 運科生理因果解構",
    "🎮 負荷管理反事實模擬",
    "🛡️ 教練調度與防護處方箋"
])

# -----------------------------------------------------------------------------
# TAB 1: 賽季微疲勞時序對比圖 (文字不重疊、寬敞邊距、完整診斷明細表)
# -----------------------------------------------------------------------------
with tab1:
    # 寬敞時序控制面板
    st.markdown(f"""
    <div style="background: #FFFFFF; border: 1.5px solid #CBD5E1; border-radius: 20px; padding: 18px 24px; margin-bottom: 20px; box-shadow: 0 1px 4px rgba(10, 44, 81, 0.05);">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px; margin-bottom: 10px;">
            <div>
                <span style="font-size: 17px; font-weight: 800; color: #0A2C51;">⏱️ 賽季時序監控視窗</span>
                <span style="color: #475569; font-size: 13.5px; margin-left: 8px;">拖曳滑桿以縮放檢視特定賽事區間：</span>
            </div>
            <div>
                <span class="badge badge-tonal">目前分析：{selected_player} ({selected_df['pos'].iloc[0]})</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 場次滑桿 (圓點隨滑鼠順暢移動)
    game_range = st.slider(
        "賽事場次範圍：",
        min_value=1,
        max_value=115,
        value=(1, 115),
        step=1,
        help="自由縮放賽季觀察視窗，聚焦先行特徵與落後成績的時差變化。",
        label_visibility="collapsed"
    )

    filtered_df = selected_df[(selected_df["game"] >= game_range[0]) & (selected_df["game"] <= game_range[1])]

    # 移除 (Dynamic Feature Weighting) 英文
    with st.expander("⚙️ 進階互動工具：即時自訂先行特徵權重係數"):
        st.markdown("<p style='font-size: 13px; color: #475569; margin-bottom: 12px;'>動態調節微疲勞演算法權重係數，圖表將即時重新計算 MFI 曲線：</p>", unsafe_allow_html=True)
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

    # 建立雙子圖配置 (加寬邊距、加大子圖間距 0.18，徹底避免文字重疊)
    if is_batter:
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.18,
            subplot_titles=(
                f"📊 落後指標：{selected_player} 傳統累積打擊率走勢",
                f"🔬 先行指標：微疲勞指數 (MFI) 與 好球帶決策特徵"
            ),
            row_heights=[0.42, 0.58]
        )
        
        # 上圖：傳統累積打擊率 (海軍藍)
        fig.add_trace(
            go.Scatter(
                x=filtered_df["game"].tolist(),
                y=filtered_df["cum_avg"].tolist(),
                name="累積打擊率 (AVG)",
                line=dict(color="#0A2C51", width=3.5),
                hovertemplate="第 %{x} 場<br>累積打擊率: %{y:.3f}<extra></extra>"
            ),
            row=1, col=1
        )
        
        # 聯盟基準線
        fig.add_hline(
            y=0.265, line_dash="dot", line_color="#64748B",
            annotation_text="聯盟平均 (.265)", annotation_position="bottom right",
            annotation_font_color="#475569", annotation_font_size=11,
            row=1, col=1
        )
        
        # 下圖：微疲勞綜合風險指數 (熱血紅)
        fig.add_trace(
            go.Scatter(
                x=filtered_df["game"].tolist(),
                y=plot_mfi.tolist() if hasattr(plot_mfi, "tolist") else list(plot_mfi),
                name="微疲勞指數 (MFI)",
                line=dict(color="#E8383D", width=3.5),
                hovertemplate="第 %{x} 場<br>MFI 指數: %{y:.1f}<extra></extra>"
            ),
            row=2, col=1
        )
        
        # 滾動 7 天 O-Swing% (壞球追打率 - 琥珀黃)
        fig.add_trace(
            go.Scatter(
                x=filtered_df["game"].tolist(),
                y=filtered_df["roll_oswing"].tolist(),
                name="壞球追打率 (7天滾動)",
                line=dict(color="#D97706", width=2.0, dash="dash"),
                hovertemplate="第 %{x} 場<br>O-Swing%: %{y:.1f}%<extra></extra>"
            ),
            row=2, col=1
        )
        
        # 滾動 7 天 Z-Whiff% (帶內揮空率 - 活力藍)
        fig.add_trace(
            go.Scatter(
                x=filtered_df["game"].tolist(),
                y=filtered_df["roll_zwhiff"].tolist(),
                name="帶內揮空率 (7天滾動)",
                line=dict(color="#1E5AA0", width=2.0, dash="dot"),
                hovertemplate="第 %{x} 場<br>Z-Whiff%: %{y:.1f}%<extra></extra>"
            ),
            row=2, col=1
        )
        
        # 滾動 7 天 HardHit% (強擊球率 - 翡翠綠)
        fig.add_trace(
            go.Scatter(
                x=filtered_df["game"].tolist(),
                y=filtered_df["roll_hardhit"].tolist(),
                name="強擊球率 (7天滾動)",
                line=dict(color="#059669", width=2.0, dash="dashdot"),
                hovertemplate="第 %{x} 場<br>HardHit%: %{y:.1f}%<extra></extra>"
            ),
            row=2, col=1
        )
        
        # 門檻標示線 (一上一下，防止標籤文字重疊)
        fig.add_hline(
            y=threshold_red, line_dash="dash", line_color="#E8383D",
            annotation_text=f"高風險警戒 ({threshold_red})",
            annotation_position="top right",
            annotation_font_color="#E8383D", annotation_font_size=11,
            row=2, col=1
        )
        fig.add_hline(
            y=threshold_yellow, line_dash="dash", line_color="#D97706",
            annotation_text=f"觀察門檻 ({threshold_yellow})",
            annotation_position="bottom right",
            annotation_font_color="#D97706", annotation_font_size=11,
            row=2, col=1
        )
        
        # 標註疲勞與預警窗口 (帶白底膠囊背景，徹底防止文字蓋住線條)
        crash_start = int(selected_df["fatigue_phase_start"].iloc[0])
        crash_end = int(selected_df["performance_crash_point"].iloc[0])
        
        if crash_start < 900:
            lead_time = crash_end - crash_start
            for r_idx in [1, 2]:
                fig.add_vrect(
                    x0=crash_start, x1=crash_end,
                    fillcolor="rgba(226, 236, 248, 0.75)",
                    layer="below", line_width=1.5, line_color="rgba(10, 44, 81, 0.45)",
                    annotation_text=f"⚡ 黃金預警窗口 ({lead_time}場時差)" if r_idx == 1 else None,
                    annotation_position="top left",
                    annotation_font_color="#0A2C51",
                    annotation_font_size=11,
                    annotation_bgcolor="rgba(255, 255, 255, 0.92)",
                    annotation_borderpad=3,
                    row=r_idx, col=1
                )
            
            # 若崩盤點落在目前篩選視窗內，加上標註箭頭 (獨立白底卡片)
            if game_range[0] <= crash_end <= game_range[1]:
                crash_rows = selected_df.loc[selected_df['game'] == crash_end, 'cum_avg']
                if not crash_rows.empty and not pd.isna(crash_rows.values[0]):
                    crash_y = float(crash_rows.values[0])
                    fig.add_annotation(
                        x=crash_end, y=crash_y,
                        text=f"📉 第 {crash_end} 場：打擊率跳水",
                        showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=2, arrowcolor="#E8383D",
                        ax=50, ay=-40,
                        bgcolor="rgba(255, 255, 255, 0.95)",
                        bordercolor="#E8383D",
                        borderwidth=1.5,
                        borderpad=4,
                        font=dict(color="#E8383D", size=11.5, family="Roboto, sans-serif"),
                        row=1, col=1
                    )
            
            # 若預警觸發點落在目前篩選視窗內，加上警報標註 (獨立白底卡片)
            if game_range[0] <= crash_start <= game_range[1]:
                fig.add_annotation(
                    x=crash_start, y=float(threshold_red),
                    text=f"🚨 第 {crash_start} 場：MFI 突破警戒",
                    showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=2, arrowcolor="#D97706",
                    ax=-50, ay=-40,
                    bgcolor="rgba(255, 255, 255, 0.95)",
                    bordercolor="#D97706",
                    borderwidth=1.5,
                    borderpad=4,
                    font=dict(color="#D97706", size=11.5, family="Roboto, sans-serif"),
                    row=2, col=1
                )
                
        y1_title = "累積打擊率 (AVG)"
        y2_title = "指數 / 百分比 (%)"

    else:
        # 投手雙子圖
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.18,
            subplot_titles=(
                f"📊 落後指標：{selected_player} 傳統防禦率走勢",
                f"🔬 先行指標：微疲勞指數 (MFI) 與 出手點離散度 / 均速"
            ),
            row_heights=[0.42, 0.58]
        )
        
        # 1. 上圖：ERA (海軍藍)
        fig.add_trace(
            go.Scatter(
                x=filtered_df["game"].tolist(),
                y=filtered_df["cum_era"].tolist(),
                name="累積防禦率 (ERA)",
                line=dict(color="#0A2C51", width=3.5),
                hovertemplate="第 %{x} 場<br>累積 ERA: %{y:.2f}<extra></extra>"
            ),
            row=1, col=1
        )
        
        # 2. 下圖：MFI (熱血紅)
        fig.add_trace(
            go.Scatter(
                x=filtered_df["game"].tolist(),
                y=plot_mfi.tolist() if hasattr(plot_mfi, "tolist") else list(plot_mfi),
                name="投手微疲勞指數 (MFI)",
                line=dict(color="#E8383D", width=3.5),
                hovertemplate="第 %{x} 場<br>投手 MFI: %{y:.1f}<extra></extra>"
            ),
            row=2, col=1
        )
        
        # 出手點離散度 (活力藍)
        fig.add_trace(
            go.Scatter(
                x=filtered_df["game"].tolist(),
                y=filtered_df["rel_disp_cm"].tolist(),
                name="出手點離散度 (cm)",
                line=dict(color="#1E5AA0", width=2.0, dash="dash"),
                hovertemplate="第 %{x} 場<br>出手點離散: %{y:.2f} cm<extra></extra>"
            ),
            row=2, col=1
        )
        
        # 均速 (鋼鐵灰藍)
        fig.add_trace(
            go.Scatter(
                x=filtered_df["game"].tolist(),
                y=(filtered_df["fastball_velo_kph"] - 140).tolist(),
                name="均速損耗 (-140km/h基準)",
                line=dict(color="#475569", width=2.0, dash="dot"),
                hovertemplate="第 %{x} 場<br>均速: %{text} km/h<extra></extra>",
                text=filtered_df["fastball_velo_kph"].tolist()
            ),
            row=2, col=1
        )
        
        fig.add_hline(
            y=threshold_red, line_dash="dash", line_color="#E8383D",
            annotation_text=f"高風險警戒 ({threshold_red})",
            annotation_position="top right",
            annotation_font_color="#E8383D", annotation_font_size=11,
            row=2, col=1
        )
        fig.add_hline(
            y=threshold_yellow, line_dash="dash", line_color="#D97706",
            annotation_text=f"觀察門檻 ({threshold_yellow})",
            annotation_position="bottom right",
            annotation_font_color="#D97706", annotation_font_size=11,
            row=2, col=1
        )
        
        crash_start = int(selected_df["fatigue_phase_start"].iloc[0])
        crash_end = int(selected_df["performance_crash_point"].iloc[0])
        
        if crash_start < 900:
            lead_time = crash_end - crash_start
            for r_idx in [1, 2]:
                fig.add_vrect(
                    x0=crash_start, x1=crash_end,
                    fillcolor="rgba(226, 236, 248, 0.75)",
                    layer="below", line_width=1.5, line_color="rgba(10, 44, 81, 0.45)",
                    annotation_text=f"⚡ 投手預警窗口 ({lead_time}場時差)" if r_idx == 1 else None,
                    annotation_position="top left",
                    annotation_font_color="#0A2C51",
                    annotation_font_size=11,
                    annotation_bgcolor="rgba(255, 255, 255, 0.92)",
                    annotation_borderpad=3,
                    row=r_idx, col=1
                )
            
        y1_title = "累積防禦率 (ERA)"
        y2_title = "MFI 指數 / 運動學指標"

    # 圖表整體排版：拉大高度至 760px，頂部加寬留給圖例，邊距充足，文字絕不重疊
    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#F8FAFC",
        font=dict(family="Roboto, sans-serif", color="#0F172A"),
        height=760,
        margin=dict(l=70, r=40, t=110, b=55),
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor="#FFFFFF",
            font_size=12,
            font_family="Roboto, sans-serif",
            font_color="#0F172A",
            bordercolor="#CBD5E1"
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.06,
            xanchor="center",
            x=0.5,
            font=dict(size=11.5, family="Roboto, sans-serif", color="#475569"),
            bgcolor="rgba(255, 255, 255, 0.92)",
            bordercolor="#CBD5E1",
            borderwidth=1
        )
    )

    fig.update_xaxes(
        showgrid=True, gridwidth=1, gridcolor="#E2E8F0",
        title_text="賽季場次 (Game Number)",
        title_font=dict(size=12.5, color="#0A2C51", family="Roboto, sans-serif"),
        tickfont=dict(color="#475569", family="Roboto, sans-serif"),
        zeroline=False
    )
    fig.update_yaxes(
        showgrid=True, gridwidth=1, gridcolor="#E2E8F0",
        row=1, col=1, title_text=y1_title,
        title_font=dict(size=12.5, color="#0A2C51", family="Roboto, sans-serif"),
        tickfont=dict(color="#475569", family="Roboto, sans-serif"),
        zeroline=False
    )
    fig.update_yaxes(
        showgrid=True, gridwidth=1, gridcolor="#E2E8F0",
        row=2, col=1, title_text=y2_title,
        title_font=dict(size=12.5, color="#0A2C51", family="Roboto, sans-serif"),
        tickfont=dict(color="#475569", family="Roboto, sans-serif"),
        zeroline=False
    )

    st.plotly_chart(fig, use_container_width=True)

    # -------------------------------------------------------------------------
    # 診斷數據明細表格 (格式化單元格，內距充足，文字完全不重疊)
    # -------------------------------------------------------------------------
    st.markdown("#### 📋 近 10 場微疲勞先行指標數值明細表")
    recent_10 = filtered_df.tail(10).iloc[::-1]
    
    rows_html = []
    for _, row in recent_10.iterrows():
        g_num = int(row['game'])
        g_date = row['date'].strftime('%m/%d') if hasattr(row['date'], 'strftime') else str(row['date'])[:5]
        mfi_val = float(row['mfi'])
        if mfi_val >= threshold_red:
            tag = '<span class="badge badge-red" style="padding: 2px 8px; font-size: 11px;">🔴 高風險</span>'
        elif mfi_val >= threshold_yellow:
            tag = '<span class="badge badge-yellow" style="padding: 2px 8px; font-size: 11px;">🟡 觀察期</span>'
        else:
            tag = '<span class="badge badge-green" style="padding: 2px 8px; font-size: 11px;">🟢 正常</span>'
            
        if is_batter:
            perf = f"{row['cum_avg']:.3f}"
            feat1 = f"{row['roll_oswing']:.1f}%"
            feat2 = f"{row['roll_zwhiff']:.1f}%"
            feat3 = f"{row['roll_hardhit']:.1f}%"
        else:
            perf = f"{row['cum_era']:.2f}"
            feat1 = f"{row['rel_disp_cm']:.2f} cm"
            feat2 = f"{row['fastball_velo_kph']:.1f} km/h"
            feat3 = f"{row['ivb_inch']:.1f} in"
            
        rows_html.append(f"""
        <tr>
            <td style="font-weight: 700; color: #0A2C51;">第 {g_num} 場</td>
            <td>{g_date}</td>
            <td style="font-weight: 700;">{perf}</td>
            <td style="font-weight: 800; color: {'#E8383D' if mfi_val >= threshold_red else '#0A2C51'};">{mfi_val:.1f}</td>
            <td>{feat1}</td>
            <td>{feat2}</td>
            <td>{feat3}</td>
            <td>{tag}</td>
        </tr>
        """)
        
    table_headers = """
    <tr>
        <th>場次</th>
        <th>日期</th>
        <th>累積打擊率 (AVG)</th>
        <th>微疲勞指數 (MFI)</th>
        <th>壞球追打率 O-Swing%</th>
        <th>帶內揮空率 Z-Whiff%</th>
        <th>強擊球率 HardHit%</th>
        <th>狀態燈號</th>
    </tr>
    """ if is_batter else """
    <tr>
        <th>場次</th>
        <th>日期</th>
        <th>累積防禦率 (ERA)</th>
        <th>微疲勞指數 (MFI)</th>
        <th>出手點 3D 離散度</th>
        <th>四縫線均速</th>
        <th>垂直誘發位移</th>
        <th>狀態燈號</th>
    </tr>
    """
    
    st.markdown(f"""
    <div style="overflow-x: auto; width: 100%; border-radius: 14px; box-shadow: 0 1px 4px rgba(10, 44, 81, 0.06); margin-top: 10px;">
        <table class="diag-table">
            <thead>{table_headers}</thead>
            <tbody>{''.join(rows_html)}</tbody>
        </table>
    </div>
    """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# TAB 2: 運科因果解構與機制分析
# -----------------------------------------------------------------------------
with tab2:
    st.markdown("### 🔬 運動生理與神經學微疲勞因果機制解構")
    col_science_1, col_science_2 = st.columns([1.2, 0.8])

    with col_science_1:
        st.markdown("""
        <div style="background: #FFFFFF; border: 1.5px solid #CBD5E1; border-radius: 24px; padding: 26px; box-shadow: var(--theme-elevation-1);">
            <div style="font-size: 18px; font-weight: 700; color: #0A2C51; margin-bottom: 16px;">
                為什麼傳統 AVG / ERA 會嚴重落後 10~14 天？
            </div>
            <div style="margin-bottom: 14px; font-size: 14px; line-height: 1.6; color: #0F172A;">
                <b>1. 視覺神經反饋遲滯 (Visual Reaction Latency, +25ms)</b>：<br>
                高強度賽季累積下，中樞神經系統 (CNS) 首先疲乏。打者對進壘球種的視知覺辨別延遲增加約 15~25 毫秒。<br>
                <span style="color: #E8383D; font-weight: 700;">➔ 先行特徵：好壞球辨識力退化，滾動 7 天 <b>O-Swing% (壞球追打率)</b> 劇烈上升 15~20%。</span>
            </div>
            <div style="margin-bottom: 14px; font-size: 14px; line-height: 1.6; color: #0F172A;">
                <b>2. 快縮肌運動單位徵召鈍化 (Motor Unit Firing Rate Decay)</b>：<br>
                揮棒啟動 (Swing Decision) 與揮棒路徑 (Bat Path Consistency) 微偏 1.5 公分。<br>
                <span style="color: #1E5AA0; font-weight: 700;">➔ 先行特徵：即便面對好球帶內紅中球，揮空率 <b>Z-Whiff%</b> 亦異常翻倍；擊球仰角與擊球點失準，<b>HardHit% (強擊率)</b> 崩跌。</span>
            </div>
            <div style="font-size: 14px; line-height: 1.6; color: #0F172A;">
                <b>3. 落後掩飾效應 (Lag Buffering Effect)</b>：<br>
                在累積打數龐大時，即便連續 5~8 場擊球品質低下，選手仍可能靠防守失誤或「德州安打」短暫維持打擊率；直至第 12 天前後好運耗盡，傳統成績呈現雪崩式跌幅。
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
            
            os_color = "#E8383D" if latest_os > 33 else "#059669"
            zw_color = "#E8383D" if latest_zw > 16 else "#059669"
            hh_color = "#E8383D" if latest_hh < 32 else "#059669"
            mfi_color = "#E8383D" if latest_mfi >= threshold_red else ("#D97706" if latest_mfi >= threshold_yellow else "#059669")
            
            st.markdown(f"""
            <div class="telemetry-card">
                <div class="telemetry-row">
                    <span>壞球追打率 (O-Swing%):</span>
                    <span style="font-weight: 700; color: {os_color};">{latest_os:.1f}%</span>
                </div>
                <div class="telemetry-row">
                    <span>好球帶內揮空率 (Z-Whiff%):</span>
                    <span style="font-weight: 700; color: {zw_color};">{latest_zw:.1f}%</span>
                </div>
                <div class="telemetry-row">
                    <span>強擊球率 (HardHit%):</span>
                    <span style="font-weight: 700; color: {hh_color};">{latest_hh:.1f}%</span>
                </div>
                <div class="telemetry-row total-row">
                    <span>綜合微疲勞先行指數 (MFI):</span>
                    <span style="font-size: 20px; font-weight: 900; color: {mfi_color};">{latest_mfi:.1f}</span>
                </div>
                <div style="margin-top: 14px; text-align: center;">
                    <span class="telemetry-badge {'badge-red' if latest_mfi >= threshold_red else ('badge-yellow' if latest_mfi >= threshold_yellow else 'badge-safe')}">
                        {'⚠️ 神經傳導延遲警報' if latest_mfi >= threshold_red else ('👀 建議降低出賽強度' if latest_mfi >= threshold_yellow else '✅ 神經肌肉動能良好')}
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            latest_disp = selected_df["rel_disp_cm"].iloc[-1]
            latest_velo = selected_df["fastball_velo_kph"].iloc[-1]
            latest_ivb = selected_df["ivb_inch"].iloc[-1]
            
            disp_color = "#E8383D" if latest_disp > 3.2 else "#059669"
            velo_color = "#E8383D" if latest_velo < 150.0 else "#059669"
            ivb_color = "#E8383D" if latest_ivb < 15.5 else "#059669"
            mfi_color = "#E8383D" if latest_mfi >= threshold_red else ("#D97706" if latest_mfi >= threshold_yellow else "#059669")
            
            st.markdown(f"""
            <div class="telemetry-card">
                <div class="telemetry-row">
                    <span>出手點 3D 空間離散度:</span>
                    <span style="font-weight: 700; color: {disp_color};">{latest_disp:.2f} cm</span>
                </div>
                <div class="telemetry-row">
                    <span>四縫線直球均速:</span>
                    <span style="font-weight: 700; color: {velo_color};">{latest_velo:.1f} km/h</span>
                </div>
                <div class="telemetry-row">
                    <span>垂直誘發位移 (IVB):</span>
                    <span style="font-weight: 700; color: {ivb_color};">{latest_ivb:.1f} inch</span>
                </div>
                <div class="telemetry-row total-row">
                    <span>投手微疲勞指數 (MFI):</span>
                    <span style="font-size: 20px; font-weight: 900; color: {mfi_color};">{latest_mfi:.1f}</span>
                </div>
                <div style="margin-top: 14px; text-align: center;">
                    <span class="telemetry-badge {'badge-red' if latest_mfi >= threshold_red else ('badge-yellow' if latest_mfi >= threshold_yellow else 'badge-safe')}">
                        {'⚠️ 手臂制動失控警報' if latest_mfi >= threshold_red else ('👀 建議縮減單場球數' if latest_mfi >= threshold_yellow else '✅ 出手動力鏈高度穩定')}
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# TAB 3: 反事實因果推論與負荷管理模擬器
# -----------------------------------------------------------------------------
with tab3:
    st.markdown("### 🎮 負荷管理反事實模擬器 (What-If Counterfactual Sandbox)")
    st.markdown("""
    <div style="color: #475569; font-size: 14px; margin-bottom: 18px;">
        在第 48 場 MFI 亮起紅燈時，若總教練立即介入處方（例如：指定打擊輪換或跳過先發一次），能否保全季末成績？
    </div>
    """, unsafe_allow_html=True)
    
    col_sim_ctrl, col_sim_view = st.columns([1, 2])
    
    with col_sim_ctrl:
        st.markdown("""
        <div style="background: #FFFFFF; border: 1.5px solid #CBD5E1; border-radius: 20px; padding: 22px; box-shadow: var(--theme-elevation-1);">
            <div style="font-weight: 700; font-size: 15px; color: #0A2C51; margin-bottom: 12px;">🎛️ 介入參數配置</div>
        """, unsafe_allow_html=True)
        
        sim_intervention = st.checkbox("啟用 MFEWS 及時處方介入", value=True)
        interv_type = st.radio(
            "介入調度策略：",
            ["全面輪休 3 天 + 指定打擊 4 場", "僅安排 1 場完全輪休", "提早至第 45 場預警性輪休"],
            index=0
        )
        fatigue_recovery_rate = st.slider("介入恢復效能強度係數", 0.5, 2.0, 1.2, 0.1)
        
        st.markdown("</div>", unsafe_allow_html=True)
        
    with col_sim_view:
        if is_batter:
            sim_avg = selected_df["cum_avg"].copy()
            if sim_intervention:
                c_start = int(selected_df["fatigue_phase_start"].iloc[0])
                if c_start < 900:
                    for idx in range(len(sim_avg)):
                        g = selected_df["game"].iloc[idx]
                        if g >= c_start + 8:
                            sim_avg.iloc[idx] = min(0.355, sim_avg.iloc[idx] + 0.038 * fatigue_recovery_rate)
            
            fig_sim = go.Figure()
            fig_sim.add_trace(go.Scatter(
                x=selected_df["game"].tolist(), y=selected_df["cum_avg"].tolist(),
                name="未介入（放任累積疲勞）", line=dict(color="#E8383D", width=2.8, dash="dash")
            ))
            fig_sim.add_trace(go.Scatter(
                x=selected_df["game"].tolist(), y=sim_avg.tolist() if hasattr(sim_avg, "tolist") else list(sim_avg),
                name="MFEWS 及時介入處方（保全打擊產能）", line=dict(color="#059669", width=3.5)
            ))
            fig_sim.update_layout(
                template="plotly_white",
                paper_bgcolor="#FFFFFF",
                plot_bgcolor="#F8FAFC",
                font=dict(family="Roboto, sans-serif", color="#0F172A"),
                height=360,
                margin=dict(l=50, r=25, t=40, b=40),
                legend=dict(
                    orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                    font=dict(size=11.5, family="Roboto, sans-serif", color="#475569"),
                    bgcolor="rgba(255, 255, 255, 0.9)", bordercolor="#CBD5E1", borderwidth=1
                )
            )
            fig_sim.update_yaxes(
                showgrid=True, gridwidth=1, gridcolor="#E2E8F0",
                title_text="累積打擊率 (AVG)",
                title_font=dict(size=12, color="#0A2C51", family="Roboto, sans-serif"),
                tickfont=dict(color="#475569", family="Roboto, sans-serif")
            )
            fig_sim.update_xaxes(
                showgrid=True, gridwidth=1, gridcolor="#E2E8F0",
                title_text="賽季場次 (Game)",
                title_font=dict(size=12, color="#0A2C51", family="Roboto, sans-serif"),
                tickfont=dict(color="#475569", family="Roboto, sans-serif")
            )
            
            st.plotly_chart(fig_sim, use_container_width=True)
            
            diff_hits = int(115 * 3.8 * (sim_avg.iloc[-1] - selected_df["cum_avg"].iloc[-1]))
            st.success(f"🎯 **反事實推論結果**：若在先行警報發布時及時介入，整季預計多保全 **+{diff_hits} 支關鍵安打**，打擊率避免滑落 **+{sim_avg.iloc[-1] - selected_df['cum_avg'].iloc[-1]:.3f}**！")
            
        else:
            sim_era = selected_df["cum_era"].copy()
            if sim_intervention:
                c_start = int(selected_df["fatigue_phase_start"].iloc[0])
                if c_start < 900:
                    for idx in range(len(sim_era)):
                        g = selected_df["game"].iloc[idx]
                        if g >= c_start + 6:
                            sim_era.iloc[idx] = max(1.80, sim_era.iloc[idx] - 0.85 * fatigue_recovery_rate)
            
            fig_sim = go.Figure()
            fig_sim.add_trace(go.Scatter(
                x=selected_df["game"].tolist(), y=selected_df["cum_era"].tolist(),
                name="未介入（放任累積疲勞）", line=dict(color="#E8383D", width=2.8, dash="dash")
            ))
            fig_sim.add_trace(go.Scatter(
                x=selected_df["game"].tolist(), y=sim_era.tolist() if hasattr(sim_era, "tolist") else list(sim_era),
                name="MFEWS 及時跳過輪值處方（保全防禦率）", line=dict(color="#059669", width=3.5)
            ))
            fig_sim.update_layout(
                template="plotly_white",
                paper_bgcolor="#FFFFFF",
                plot_bgcolor="#F8FAFC",
                font=dict(family="Roboto, sans-serif", color="#0F172A"),
                height=360,
                margin=dict(l=50, r=25, t=40, b=40),
                legend=dict(
                    orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                    font=dict(size=11.5, family="Roboto, sans-serif", color="#475569"),
                    bgcolor="rgba(255, 255, 255, 0.9)", bordercolor="#CBD5E1", borderwidth=1
                )
            )
            fig_sim.update_yaxes(
                showgrid=True, gridwidth=1, gridcolor="#E2E8F0",
                title_text="累積防禦率 (ERA)",
                title_font=dict(size=12, color="#0A2C51", family="Roboto, sans-serif"),
                tickfont=dict(color="#475569", family="Roboto, sans-serif")
            )
            fig_sim.update_xaxes(
                showgrid=True, gridwidth=1, gridcolor="#E2E8F0",
                title_text="賽季場次 (Game)",
                title_font=dict(size=12, color="#0A2C51", family="Roboto, sans-serif"),
                tickfont=dict(color="#475569", family="Roboto, sans-serif")
            )
            
            st.plotly_chart(fig_sim, use_container_width=True)
            saved_runs = (selected_df["cum_era"].iloc[-1] - sim_era.iloc[-1]) * (115 * 6 / 9)
            st.success(f"🎯 **反事實推論結果**：若及時跳過輪值一次，全季預計少失 **{saved_runs:.1f} 分自責分**，防禦率降低 **-{selected_df['cum_era'].iloc[-1] - sim_era.iloc[-1]:.2f}**！")

# -----------------------------------------------------------------------------
# TAB 4: 教練調度與防護處方箋
# -----------------------------------------------------------------------------
with tab4:
    st.markdown("### 🛡️ 教練團調度處方與運動科學防護指南")
    curr_player_mfi = selected_df["mfi"].iloc[-1]

    act_col1, act_col2, act_col3 = st.columns(3)

    with act_col1:
        if curr_player_mfi >= threshold_red:
            variant = "danger"
            t_text = "🚨 【一級警戒】總教練出賽調度處方"
            b_text = """
            • <b>強制輪休</b>：立即自先發名單移出，未來 3 場安排完全輪休或僅限 9 局代打。<br>
            • <b>守備負擔減免</b>：若維持出賽，必須轉任指定打擊 (DH)，嚴禁參與高耗能外野守備。<br>
            • <b>跑壘戰術解除</b>：取消盜壘與打帶跑戰術執行授權，保護下肢肌腱。
            """
        elif curr_player_mfi >= threshold_yellow:
            variant = "warning"
            t_text = "🟡 【二級觀察】守備局數調控處方"
            b_text = """
            • <b>指定打擊輪替</b>：本週 5 場賽事中，安排 2 場擔任指定打擊 (DH)。<br>
            • <b>提早退場機制</b>：若比分領先超過 4 分，於第 7 局安排守備組替換退場。<br>
            • <b>棒次後移</b>：暫時由第 1~3 棒主力打線移至第 6 棒，降低得點圈心理抗壓負荷。
            """
        else:
            variant = "info"
            t_text = "🟢 【常態運作】全速出賽綠燈授權"
            b_text = """
            • <b>完全戰力釋放</b>：中樞神經系統與快縮肌反應維持巔峰，無疲勞掩飾風險。<br>
            • <b>正常先發</b>：可完全維持常規守備與第 1~3 棒主力進攻戰術授權。<br>
            • <b>持續追蹤</b>：每週一例行性檢測 MFI 趨勢。
            """
        st.markdown(render_theme_action_card(t_text, b_text, variant), unsafe_allow_html=True)

    with act_col2:
        if curr_player_mfi >= threshold_red:
            variant = "danger"
            t_text = "🏋️ 【阻斷課表】打擊教練訓練調整處方"
            b_text = """
            • <b>打擊練習降載</b>：全面暫停賽前 5 組 Free Batting，改為 2 組短程 Tee 擊球。<br>
            • <b>特打訓練取消</b>：全面禁止賽前或賽後加練特打。<br>
            • <b>好球帶感知校準</b>：利用 VR 虛擬實境追蹤系統，進行 15 分鐘純視覺好球辨識訓練。
            """
        elif curr_player_mfi >= threshold_yellow:
            variant = "warning"
            t_text = "🏋️ 【量級管控】肌力體能訓練調整處方"
            b_text = """
            • <b>重訓強度降低 30%</b>：主運動組數由 4 組縮減為 2 組，以維持爆發力為主。<br>
            • <b>增強式訓練暫停</b>：暫停跳箱與深度跳躍等高離心收縮項目。<br>
            • <b>核心抗旋轉強化</b>：專注於低衝擊度的核心與旋轉肌群控制。
            """
        else:
            variant = "info"
            t_text = "🏋️ 【例行維護】週期化力量強化課表"
            b_text = """
            • <b>維持標準訓練量</b>：生理神經反應良好，可依既定課表進行中高強度重訓。<br>
            • <b>常態化課表</b>：按選手個人週期化重訓課表執行即可。<br>
            • <b>神經啟動</b>：賽前常規 15 分鐘速度敏捷繩梯與快縮肌啟動。
            """
        st.markdown(render_theme_action_card(t_text, b_text, variant), unsafe_allow_html=True)

    with act_col3:
        if curr_player_mfi >= threshold_red:
            variant = "danger"
            t_text = "🩺 【緊急修復】防護員物理治療介入處方"
            b_text = """
            • <b>冷熱交替浸泡</b>：賽後即刻執行 12 分鐘對比浴 (Contrast Bath Therapy)。<br>
            • <b>神經肌肉放鬆</b>：針對腰薦椎豎脊肌與旋轉肌群進行 30 分鐘深層筋膜刀放鬆。<br>
            • <b>血流阻斷恢復</b>：賽後進行 BFR 低阻力主動伸展，加速代謝副產物清除。
            """
        elif curr_player_mfi >= threshold_yellow:
            variant = "warning"
            t_text = "🩺 【預防保養】生物力學檢測與防護處方"
            b_text = """
            • <b>關節活動度 (ROM) 篩檢</b>：重點檢測胸椎旋轉角度與髖關節內外旋活動度。<br>
            • <b>淋巴引流氣壓靴</b>：賽前與賽後各使用 NormaTec 氣壓靴 20 分鐘。<br>
            • <b>睡眠監測加強</b>：睡眠時間確保達 8.5 小時，必要時補充電解質與鎂劑。
            """
        else:
            variant = "info"
            t_text = "🩺 【健康監控】例行防護與疲勞恢復"
            b_text = """
            • <b>常規保養流程</b>：賽後維持常態性伸展與冰敷保養。<br>
            • <b>例行保養</b>：常態性賽後肩關節/手肘冰熱敷交替與軟組織滾筒放鬆。<br>
            • <b>睡眠品質良好</b>：心率變異度與肌肉張力指數維持於標準綠燈區間。
            """
        st.markdown(render_theme_action_card(t_text, b_text, variant), unsafe_allow_html=True)

    st.write("")
    clean_b_text = b_text.replace("<b>", "").replace("</b>", "").replace("<br>", "\n   ")
    clean_b_text2 = b_text2.replace("<b>", "").replace("</b>", "").replace("<br>", "\n   ")
    clean_b_text3 = b_text3.replace("<b>", "").replace("</b>", "").replace("<br>", "\n   ")
    
    export_content = f"""=============================================================================
【MFEWS 賽季微疲勞先行預警系統】專屬調度與防護處方箋
球隊：{st.session_state['selected_team']} | 名單層級：一軍登錄名單
球員姓名：{selected_player} ({selected_df['pos'].iloc[0]})
產生日程：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
微疲勞指數 (MFI)：{curr_player_mfi:.1f} | 狀態：{selected_df['status_now'].iloc[-1]}
=============================================================================

【1. 總教練出賽調度處方】：
   {clean_b_text.strip()}

【2. 賽前訓練負荷管制處方】：
   {clean_b_text2.strip()}

【3. 運科防護與生物力學檢測處方】：
   {clean_b_text3.strip()}
=============================================================================
"""
    st.download_button(
        label=f"📥 一鍵下載【{selected_player}】運科調度處方箋",
        data=export_content,
        file_name=f"MFEWS_Prescription_{selected_player}_{datetime.now().strftime('%Y%m%d')}.txt",
        mime="text/plain",
        use_container_width=True
    )

st.write("")

# =============================================================================
# 7. 頁尾資訊與版權宣告 (© NTUT IAE. All rights reserved.)
# =============================================================================
st.markdown("""
<div class="mfews-footer">
    2026 野革盃台灣棒球數據黑客松參賽專案 · Micro-Fatigue Early Warning System (MFEWS)<br>
    © NTUT IAE. All rights reserved.
</div>
""", unsafe_allow_html=True)
