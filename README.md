# ⚾ MFEWS | 賽季微疲勞先行指標預警系統
### Micro-Fatigue Early Warning System (MFEWS)
> **2026 野革盃台灣棒球數據黑客松 · 參賽專案**  
> *「等成績跳水才換人，球員早已過勞兩週；以神經視覺與微觀動力學先行特徵，奪回 10~14 天黃金調度主動權。」*

[![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)](https://streamlit.io/)
[![Plotly](https://img.shields.io/badge/Plotly-5.18+-3F4F75?style=for-the-badge&logo=Plotly&logoColor=white)](https://plotly.com/)
[![WebAssembly](https://img.shields.io/badge/WebAssembly-Stlite_Wasm-654FF0?style=for-the-badge&logo=webassembly&logoColor=white)](https://github.com/whitphx/stlite)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

---

## 📖 專案核心論述 (Core Philosophy)

傳統棒球數據分析中，**打擊率（AVG）** 與 **防禦率（ERA）** 是典型的**落後指標（Lagging Indicators）**。  
在現代高張力長賽季中，當一名核心打者的打擊率開始從 `.330` 墜崖式跌至 `.280`，或王牌投手的單月 ERA 暴增時，運動生理學與運動醫學研究顯示：**該球員的神經肌肉微疲勞（Neuromuscular Micro-Fatigue）往往已累積超過兩週（10 至 14 天）**。

在疲勞剛開始累積的初期（第 1~10 天），打者往往能依靠龐大的累積打數基期、守備失誤、甚至受惠於球場運氣（BABIP 雜訊）維持表面的傳統成績；然而，其神經肌肉系統早已發出警訊。若教練團持續放任先發，將導致：
1. **運動傷害風險暴增**：腹斜肌拉傷、膝蓋髕骨肌腱炎、手肘 UCL 韌帶拉扯代償。
2. **陷入深度打擊/投球低潮**：長達 3~4 週陷入打擊泥淖，單季 WAR 大幅損耗。

**MFEWS（賽季微疲勞先行指標預警系統）** 專注於擷取**好球帶決策神經反饋**與**微觀生物力學運動學特徵**（滾動 7 天 `O-Swing%`、`Z-Whiff%`、`HardHit%`，以及投手出手點 3D 空間離散度），構建**微疲勞綜合風險指數（Micro-Fatigue Index, MFI）**。系統能在選手傳統成績崩盤前 **10 至 14 天（約 12 場賽事）** 即刻亮燈預警，讓教練團進行精準的**負荷管理（Load Management）**。

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

## 🖥️ 大聯盟戰情室系統功能亮點

1. **Google Material You (Material Design 3 - MD3) 現代戰情 UI**：
   - 全面導入 Material You (MD3) 規範：經典紫色種子調色盤（Seed Color `#6750A4`）、淺色 Tonal Surface 色彩層級、大圓角容器（24px ~ 36px）與藥丸型態狀態標籤（Pill Badges）。
   - 注入有機氛圍背景微動效（Layered Organic Blur Shapes）、多層陰影階度（Elevation Levels 1~3）與流暢觸覺微動效反饋（Active Scale 95）。
   - 頂部隊伍健康指數（THI）、高風險疲勞人數、平均領先時差（12.4 天）、預防介入成功率四大戰情 KPI 卡片。
   - 6 位全隊主力球員（含先發外野手、內野手、捕手、先發投手）即時燈號矩陣。
2. **時序對比圖表（Plotly Subplots）**：
   - 垂直同步雙圖：上方呈現「累積打擊率/防禦率（落後指標）」，下方呈現「MFI 與三大先行指標」。
   - 高亮半透明金色色塊標記「10~14 天黃金預警窗口」，直觀呈現警報發出與傳統跳水之間的時差。
3. **負荷管理反事實模擬器（Counterfactual Simulator）**：
   - 點選切換開關，即刻對比「若在第 48 場及時介入」vs「放任疲勞至第 60 場崩盤」的打擊率走勢預測。
   - 實時計算保全之 **+0.82 勝場貢獻值（WAR）** 與受傷風險降幅。
4. **教練調度與防護建議卡（Actionable Prescriptions）**：
   - 即時輸出三大面向處方：
     - **戰術與陣容調度**（DH 輪替、降次棒次、局數管控）。
     - **賽前訓練負荷管制**（Live BP 減量 60%、禁用加重棒、改採 VR 視知覺訓練）。
     - **運科防護與生物力學檢測**（測力板反向跳 CMJ 發力對稱性、關節活動度、低溫冷凍艙）。

---

## 🚀 本地端安裝與啟動步驟 (Local Quickstart)

### 步驟 1：複製儲存庫
```bash
git clone https://github.com/your-username/baseball-mfews.git
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

## 🌐 GitHub Pages 一鍵部署指南 (Serverless via WebAssembly)

本專案完全支援 **純前端 WebAssembly（stlite）** 執行！無需任何後端伺服器（免 EC2、免 Heroku、免付費主機），只需啟用 GitHub Pages 即可永久免費對外展示：

### 部署步驟：
1. 將專案推送到您的 GitHub 儲存庫：
   ```bash
   git add .
   git commit -m "feat: 2026 野革盃 MFEWS 微疲勞預警戰情室"
   git push origin main
   ```
2. 進入該 GitHub 專案的 **Settings** -> **Pages**。
3. 在 **Build and deployment** 下：
   - Source 選擇：`Deploy from a branch`
   - Branch 選擇：`main` / Folder 選擇：`/(root)`
   - 點擊 **Save**。
4. 約 1~2 分鐘後，即可透過 `https://<your-username>.github.io/<repo-name>/` 直接進入線上互動戰情室！
   *(載入時會在瀏覽器透過 WebAssembly 啟動 Pyodide 並運算所有運動力學數據，零伺服器成本！)*

---

## 📁 檔案結構 (Project Structure)

```
baseball-mfews/
├── app.py              # 檔案 1：Streamlit 完整戰情室主程式 (包含運動學模擬、MFI、Plotly 雙子圖與處方卡片)
├── requirements.txt    # 檔案 2：最小本地端環境相依套件清單 (streamlit, pandas, numpy, plotly)
├── README.md           # 檔案 3：黑客松完整參賽技術文件與運科原理
└── index.html          # 檔案 4：GitHub Pages 專用 stlite (WebAssembly) 免後端一鍵包裝檔
```

---

## 🏆 2026 野革盃台灣棒球數據黑客松參賽宣告

- **專案主題**：賽季微疲勞先行指標預警系統（Micro-Fatigue Early Warning System, MFEWS）
- **核心價值**：跨越落後指標盲區，打造具備大聯盟球團戰情室規格的運動科學決策輔助系統。
- **開源授權**：MIT License
