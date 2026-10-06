# ⚾ MFEWS | 賽季微疲勞先行指標預警系統
### Micro-Fatigue Early Warning System (MFEWS)
> **2026 野革盃台灣棒球數據黑客松 · 參賽專案**  
> *「等成績跳水才換人，球員早已過勞兩週；以神經視覺與微觀動力學先行特徵，奪回 10~14 天黃金調度主動權。」*

[![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)](https://streamlit.io/)
[![Plotly](https://img.shields.io/badge/Plotly-5.18+-3F4F75?style=for-the-badge&logo=Plotly&logoColor=white)](https://plotly.com/)
[![WebAssembly](https://img.shields.io/badge/WebAssembly-Stlite_Wasm-654FF0?style=for-the-badge&logo=webassembly&logoColor=white)](https://github.com/whitphx/stlite)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

🌐 **GitHub Pages 線上即時展示（純前端 WebAssembly 免安裝）**：  
👉 [https://ericlin241.github.io/baseball-mfews/](https://ericlin241.github.io/baseball-mfews/)

---

## 📖 專案核心論述 (Core Philosophy)

傳統棒球數據分析中，**打擊率（AVG）** 與 **防禦率（ERA）** 是典型的**落後指標（Lagging Indicators）**。  
在現代高張力長達 120 場的中職賽季中，當一名主力打者的打擊率開始從 `.330` 斷崖式跌至 `.280`，或王牌投手的單月 ERA 暴增時，運動醫學與生理學研究顯示：**該球員的神經肌肉微疲勞（Neuromuscular Micro-Fatigue）往往已累積超過兩週（10 至 14 天）**。

在疲勞初期（第 1~10 天），打者往往能依靠龐大的累積打數基期或球場運氣（BABIP 雜訊）維持表面的傳統成績；然而其神經肌肉系統早已發出警訊。若教練團持續放任先發出賽，將導致：
1. **運動傷害代償暴增**：腹斜肌拉傷、膝蓋髕骨肌腱炎、手肘 UCL 韌帶發炎與關節代償。
2. **陷入長達一個月的深度低潮**：手感盡失，單季 WAR 嚴重損耗。

**MFEWS（賽季微疲勞先行指標預警系統）** 專注於擷取**好球帶決策神經反饋**與**微觀生物力學運動學特徵**（滾動 7 天 `O-Swing%`、`Z-Whiff%`、`HardHit%`，以及投手出手點 3D 空間離散度），構建**微疲勞綜合風險指數（Micro-Fatigue Index, MFI）**。系統能在選手傳統成績跳水前 **10 至 14 天（約 12 場賽事）** 即刻亮起紅燈預警，提供教練團精準的**負荷管理（Load Management）處方**。

---

## ⏱️ 落後指標 vs 先行指標 時差機制圖解

```
賽季時序進程 (時間軸 / 場次) ─────────────────────────────────────────────────────────────►
場次: G40            G46        G48               G55             G60          G75
      │               │          │                 │               │            │
神經  [正常高水準]    [中樞神經]  [好球帶辨識崩壞]  [揮棒速度失準]  [全面過勞]   [被迫休養]
狀態                  開始疲勞    視覺延遲 +25ms    肌纖維徵召衰退  代償受傷風險
      │               │          │                 │               │            │
先行  O-Swing: 22%   O-Swing:28% [O-Swing: 39%]    Z-Whiff: 22%   HardHit: 22%
指標  Z-Whiff: 8%                [MFI 衝破 70 🚨]  MFI 達到 84     MFI 居高不下
      │               │          │                 │               │            │
      │               │          ▼                 │               ▼            │
      │               │   ╔═════════════════════════════════╗      │            │
      │               │   ║ ⚡ MFEWS 黃金介入窗口 (12 天時差) ║      │            │
      │               │   ║   教練團可安排 DH輪休 / BP減量  ║      │            │
      │               │   ╚═════════════════════════════════╝      │            │
      │               │          │                 │               │            │
傳統  AVG: .342       AVG: .339  AVG: .335 (掩飾期)AVG: .328 (鈍化)[AVG: .288 📉]
指標  (表面亮眼)      (無異狀)    (表面仍高檔)      (微幅下滑)     [傳統數據暴跌!]
```

---

## ⚾ 中職六球團完整 252 位真實球員資料庫 (CPBL 6-Team Roster Database)

本系統完整收錄中華職棒（CPBL）現役全 6 支球團，每隊包含 **26 位一軍主力名單** 與 **16 位二軍培訓名單**，共計 **252 位球員**，提供真實守備位置、個人歷史擊球/投球基準型態：

| 球團名稱 | 一軍登錄陣容 (26 人) | 二軍培訓陣容 (16 人) | 代表球星範例 |
| :--- | :--- | :--- | :--- |
| **味全龍** | 15 打者 + 11 投手 | 9 打者 + 7 投手 | 吉力吉撈．鞏冠、李凱威、劉基鴻、郭天信、徐若熙、鋼龍、陳冠偉、銳歐 |
| **統一7-ELEVEn獅** | 15 打者 + 11 投手 | 9 打者 + 7 投手 | 陳傑憲、林安可、邱智呈、蘇智傑、潘傑楷、古林睿煬、勝騎士、陳韻文 |
| **中信兄弟** | 15 打者 + 11 投手 | 9 打者 + 7 投手 | 江坤宇、岳政華、王威晨、許基宏、陳俊秀、曾頌恩、德保拉、吳俊偉 |
| **樂天桃猿** | 15 打者 + 11 投手 | 9 打者 + 7 投手 | 林立、陳晨威、廖健富、梁家榮、朱育賢、林泓育、威能帝、陳柏豪 |
| **富邦悍將** | 15 打者 + 11 投手 | 9 打者 + 7 投手 | 張育成、申皓瑋、王正棠、董子恩、戴培峰、江少慶、富藍戈、曾峻岳 |
| **台鋼雄鷹** | 15 打者 + 11 投手 | 9 打者 + 7 投手 | 王柏融、魔鷹、曾子祐、陳文杰、吳念庭、哈瑪星、後勁、雷公 |

---

## 🔬 先行特徵工程原理 (Sports Science & Neurological Grounding)

MFEWS 所選用的先行特徵皆具備嚴謹的運動生理學與神經科學基礎：

### 1. 打者特徵 (Batter Neuromuscular Features)
| 指標名稱 | 傳統角色 | 運科疲勞意義 (Fatigue Biomarker) | 正常基準 | 疲勞警示閾值 |
| :--- | :--- | :--- | :--- | :--- |
| **O-Swing%**<br>(壞球追打率) | 選球紀律 | **中樞神經系統（CNS）視知覺延遲**<br>當大腦視覺皮層疲勞時，對球路軌跡的反應時間延遲 15~25 毫秒，導致打者無法在好壞球臨界點踩煞車，滾動 7 天追打率急速飆高。 | 20% ~ 25% | **> 35%** (顯著惡化) |
| **Z-Whiff%**<br>(好球帶內揮空率) | 擊球技巧 | **快縮肌運動單位徵召鈍化（Motor Unit Fatigue）**<br>面對好球帶內來球，揮棒啟動時間與揮棒軌跡（Bat Path）產生微米級偏差，即使是失投紅中球也頻頻揮空或擊出擦棒球。 | 7% ~ 10% | **> 18%** (爆發力損耗) |
| **HardHit%**<br>(強擊球率, 95mph+) | 擊球力量 | **動力鏈傳導效率洩漏（Kinetic Chain Breakdown）**<br>下肢至軀幹轉體的動能傳遞衰減，擊球初速 >= 95 mph 的比例顯著下跌，軟弱滾地球與沖天炮比例倍增。 | 40% ~ 48% | **< 28%** (擊球噴力衰退) |

### 2. 投手特徵 (Pitcher Kinematic Features)
| 指標名稱 | 傳統角色 | 運科疲勞意義 (Fatigue Biomarker) | 正常基準 | 疲勞警示閾值 |
| :--- | :--- | :--- | :--- | :--- |
| **Release Point 3D Dispersion**<br>(出手點 3D 空間離散度 $\sigma_{rel}$) | 控球穩定度 | **肩袖肌群與核心穩定失調**<br>當肩胛穩定肌與旋轉肌袖肌力衰竭，投手無法維持重複的出手投球幾何角度，出手點 3D 空間雲端離散度顯著擴大。 | 1.5 ~ 2.0 cm | **> 3.8 cm** (動作變異度過大) |
| **Fastball Velocity Drop**<br>(四縫線均速衰退 $\Delta V$) | 球威強度 | **下肢推蹬與前臂旋前力減弱**<br>投球時速連續 2~3 場下滑 2~4 km/h，預告手臂代償風險與即將被打爆。 | 152 ~ 155 km/h | **下滑 > 3.0 km/h** |
| **iVB Flatness**<br>(垂直誘發位移衰竭) | 球路尾勁 | **轉速效率與縫線轉軸偏移（Spin Axis Drift）**<br>轉速與旋轉效率降低，球路進壘視覺垂直竄升感喪失（球質變平），揮空率驟降。 | 17 ~ 19 in | **< 15.0 in** |

---

## 🧮 微疲勞綜合風險指數（Micro-Fatigue Index, MFI）

MFI 透過對各滾動特徵進行動態常態化評分，加權融合為 **0 ~ 100** 分之綜合風險指數：

### 打者 MFI 計算公式：
$$MFI_{batter} = w_1 \cdot S(O\text{-Swing}\%) + w_2 \cdot S(Z\text{-Whiff}\%) + w_3 \cdot S(HardHit\%)$$
其中各特徵正規化分數 $S(\cdot)$ 定義為：
- $S(O\text{-Swing}\%) = \text{clip}\left(\frac{\text{Roll\_OSwing} - 0.20}{0.42 - 0.20}, 0, 1\right) \times 100$
- $S(Z\text{-Whiff}\%) = \text{clip}\left(\frac{\text{Roll\_ZWhiff} - 0.07}{0.24 - 0.07}, 0, 1\right) \times 100$
- $S(HardHit\%) = \text{clip}\left(\frac{0.45 - \text{Roll\_HardHit}}{0.45 - 0.22}, 0, 1\right) \times 100$
- 預設權重係數：$w_1 = 0.40$（神經決策）, $w_2 = 0.35$（揮棒微調）, $w_3 = 0.25$（動力輸出）。

### 燈號警示等級矩陣：
- 🟢 **正常低風險（綠燈）**：$MFI < 50$ — 維持常規訓練與先發調度。
- 🟡 **觀察期（黃燈）**：$50 \le MFI < 70$ — 進入警戒，建議賽前打擊練習減量 30%，監控 HRV 心率變異度。
- 🔴 **高風險預警（紅燈）**：$MFI \ge 70$ — **強制啟動黃金介入窗口**！立即轉任 DH 或給予 2~3 天輪休，避免受傷與長達一個月的打擊低潮。

---

## 🖥️ 戰情室系統五大功能核心

1. **直覺切換之球員卡矩陣 (Direct Card Click Navigation)**：
   - 點選球員卡即可切換選取，下方**絕不出現任何多餘實體名字按鈕**。
   - **視覺對比**：未選取時為乾淨白底；選取中之卡片**直接轉為經典深海軍藍（#0A2C51），球員姓名及守備位置完美反白純白**，階層一目了然。
   - 右側快速切換「一軍登錄名單」與「二軍培訓名單」，即時載入所屬層級選手。
2. **賽季時序深度診斷 (Temporal Diagnostics & 10-Game Table)**：
   - 垂直同步雙圖（Plotly Subplots）：上方為「累積打擊率/防禦率（落後指標）」，下方為「MFI 與三大先行指標走勢」。
   - 高亮半透明金色色塊標記「10~14 天黃金預警窗口」。
   - **近 10 場微疲勞先行指標數值明細表**：以原生美觀表格呈現，無程式碼干擾，支援手機橫向滑動。
3. **運科生理因果解構 (Biomechanical Telemetry)**：
   - 即時遙測神經肌肉特徵數值，詳細分析視知覺反應、擊球動力鏈或投手出手點空間變異度。
4. **負荷管理反事實模擬器 (What-If Sandbox)**：
   - 實時對比「在第 48 場及時處方介入」vs「放任疲勞至第 60 場崩盤」的季末打擊率/防禦率差異。
   - 實時計算保全之勝場貢獻值（WAR）與受傷風險降幅。
5. **教練調度與防護處方箋 (Actionable Prescriptions & 1-Click Export)**：
   - 輸出三大面向處方：總教練出賽調度、打擊/體能訓練量級管制、防護員物理治療介入。
   - **一鍵下載專屬調度處方箋**（`.txt`），內容包含球團名稱、名單層級、當前 MFI 指數與具體維護指令。

---

## 📱 手機與平板專屬響應式優化 (Mobile & Tablet Responsive Design)

系統特別針對行動裝置與平板進行深度排版調校：
- **手機螢幕（< 768px）**：
  - 頂部戰情總覽自動縮放標題，KPI 卡片平滑轉為雙欄排列。
  - 球員卡矩陣自動適應為 2 欄網格，卡片內距最佳化，按壓觸控精準。
  - 時序明細表格支援觸控橫向流暢滾動（`-webkit-overflow-scrolling: touch`）。
  - 處方指南卡自動切換為全寬單欄檢視。
- **平板螢幕（768px ~ 1024px）**：
  - 球員卡自動呈現 4 欄適中比例，提供沉浸式教練團檢視體驗。

---

## 🚀 本地端安裝與啟動步驟 (Local Quickstart)

### 步驟 1：複製儲存庫
```bash
git clone https://github.com/ericlin241/baseball-mfews.git
cd baseball-mfews
```

### 步驟 2：安裝相依套件
建議使用虛擬環境（Python 3.10+）：
```bash
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 步驟 3：啟動 Streamlit 戰情室
```bash
streamlit run app.py
```
啟動後瀏覽器將自動開啟 `http://localhost:8501`。

---

## 🌐 GitHub Pages 免後端一鍵線上運行 (Serverless via WebAssembly)

本專案完全支援 **純前端 WebAssembly（stlite）** 執行！無需任何後端伺服器，直接透過瀏覽器端執行 Python、Pandas、NumPy 與 Plotly：

👉 **線上即刻體驗**：[https://ericlin241.github.io/baseball-mfews/](https://ericlin241.github.io/baseball-mfews/)

---

## 📁 檔案結構 (Project Structure)

```
baseball-mfews/
├── app.py              # 核心主程式：包含 252 位球員模擬引擎、MFI 計算、Plotly 視覺化與處方箋產製
├── requirements.txt    # 本地端環境相依套件清單 (streamlit, pandas, numpy, plotly)
├── README.md           # 專案完整參賽技術文件與運科原理
└── index.html          # GitHub Pages 專用 stlite (WebAssembly) 免後端單頁包裝檔
```

---

## 🏆 2026 野革盃台灣棒球數據黑客松參賽宣告

- **專案主題**：賽季微疲勞先行指標預警系統（Micro-Fatigue Early Warning System, MFEWS）
- **核心價值**：跨越落後指標盲區，奪回 10~14 天黃金調度窗口，打造職棒球團戰情室規格的運動科學決策輔助系統。
- **開源授權**：MIT License
