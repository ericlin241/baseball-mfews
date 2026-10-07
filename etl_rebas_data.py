"""
ETL Pipeline: Integrate rebas.tw Open Data into MFEWS
Robust rolling-window analytics for O-Swing%, Z-Whiff%, and HardHit%
Source: https://github.com/rebas-tw/rebas.tw-open-data (CPBL 2024 Season)
"""

import zipfile
import json
from datetime import datetime, timedelta
from collections import defaultdict
import numpy as np

def safe_float(val):
    if not val:
        return None
    try:
        s = ''.join(c for c in str(val) if c in '0123456789.-')
        if s and s != '-' and s != '.':
            return float(s)
    except Exception:
        pass
    return None

def main():
    print("=== [MFEWS ETL] Running High-Precision Rolling Window Calculation from REBAS 2024 ===")

    # 1. Load current database template
    with open('players_data.json', 'r', encoding='utf-8') as f:
        target_players = json.load(f)

    # 2. Extract and organize all game JSONs
    with zipfile.ZipFile('cpbl_2024.zip', 'r') as z:
        game_files = [n for n in z.namelist() if n.endswith('.json') and 'G' in n]
        def get_gnum(name):
            try:
                base = name.split('/')[-1].replace('.json', '')
                return int(base.split('-G')[-1])
            except Exception:
                return 9999
        game_files.sort(key=get_gnum)

        pitcher_raw_logs = defaultdict(list)
        batter_raw_logs = defaultdict(list)

        print(f"Parsing {len(game_files)} game files...")
        for gfile in game_files:
            try:
                with z.open(gfile) as gf:
                    g = json.load(gf)
            except Exception:
                continue

            g_date = g.get('date', '')[:10]
            if not g_date:
                continue
            mm_dd = g_date[5:].replace('-', '/')

            all_pa = g.get('awayPAList', []) + g.get('homePAList', [])
            pa_by_pitcher = defaultdict(list)
            pa_by_batter = defaultdict(list)

            for pa in all_pa:
                p_name = pa.get('pitcherName')
                b_name = pa.get('batterName')
                if p_name:
                    pa_by_pitcher[p_name].append(pa)
                if b_name:
                    pa_by_batter[b_name].append(pa)

            # --- Process Pitchers ---
            all_pitchers = g.get('awayPitcherBox', []) + g.get('homePitcherBox', [])
            for p in all_pitchers:
                p_name = p.get('playerName')
                if not p_name:
                    continue

                pas = pa_by_pitcher.get(p_name, [])
                pitches = []
                for pa in pas:
                    for ev in pa.get('events', []):
                        if ev.get('type') == 'PITCH':
                            pitches.append(ev)

                ff_vels = []
                all_vels = []
                xs = []
                ys = []
                for ev in pitches:
                    v = safe_float(ev.get('velocity'))
                    x = safe_float(ev.get('coordX'))
                    y = safe_float(ev.get('coordY'))
                    if v and v > 80:
                        all_vels.append(v)
                        if ev.get('pitchType') == 'FF':
                            ff_vels.append(v)
                    if x is not None:
                        xs.append(x)
                    if y is not None:
                        ys.append(y)

                avg_ff = float(np.mean(ff_vels)) if ff_vels else (float(np.mean(all_vels)) if all_vels else None)
                disp_cm = float(np.std(xs)) / 10.0 if len(xs) >= 4 else None
                vert_mov = float(np.mean(np.abs(ys))) / 10.0 if ys else None

                pitcher_raw_logs[p_name].append({
                    'date': mm_dd,
                    'full_date': g_date,
                    'np': int(p.get('NP', 0)),
                    'ip_outs': int(p.get('IPOuts', 0)),
                    'er': int(p.get('ER', 0)),
                    'h': int(p.get('H', 0)),
                    'so': int(p.get('SO', 0)),
                    'bb': int(p.get('BB', 0)),
                    'avg_ff': avg_ff,
                    'disp_cm': disp_cm,
                    'vert_mov': vert_mov
                })

            # --- Process Batters ---
            all_batters = g.get('awayBatterBox', []) + g.get('homeBatterBox', [])
            for b in all_batters:
                b_name = b.get('playerName')
                if not b_name:
                    continue

                pas = pa_by_batter.get(b_name, [])
                pitches = []
                for pa in pas:
                    for ev in pa.get('events', []):
                        if ev.get('type') == 'PITCH':
                            pitches.append(ev)

                # Count zone swings & misses with exact strike zone bounds
                o_pitches = 0
                o_swings = 0
                z_pitches = 0
                z_swings = 0
                z_whiffs = 0

                for ev in pitches:
                    x = safe_float(ev.get('coordX'))
                    y = safe_float(ev.get('coordY'))
                    pcode = ev.get('pitchCode')
                    is_swing = pcode in ['SW', 'F', 'FT', 'H', 'TRY_BUNT', 'FOUL_BUNT', 'BUNT']
                    is_whiff = pcode in ['SW', 'TRY_BUNT']

                    # Strike zone rectangle: |coordX| <= 65 and |coordY| <= 60
                    if x is not None and y is not None:
                        in_zone = (abs(x) <= 65.0 and abs(y) <= 60.0)
                    else:
                        in_zone = (ev.get('isStrike') is True)

                    if in_zone:
                        z_pitches += 1
                        if is_swing:
                            z_swings += 1
                            if is_whiff:
                                z_whiffs += 1
                    else:
                        o_pitches += 1
                        if is_swing:
                            o_swings += 1

                # Hardness: H = Hard, M = Medium, S = Soft
                hard_hits = sum(1 for pa in pas if pa.get('hardness') == 'H')
                batted_balls = sum(1 for pa in pas if pa.get('hardness') in ['H', 'M', 'S'])

                batter_raw_logs[b_name].append({
                    'date': mm_dd,
                    'full_date': g_date,
                    'ab': int(b.get('AB', 0)),
                    'h': int(b.get('H', 0)),
                    'o_pitches': o_pitches,
                    'o_swings': o_swings,
                    'z_pitches': z_pitches,
                    'z_swings': z_swings,
                    'z_whiffs': z_whiffs,
                    'hard_hits': hard_hits,
                    'batted_balls': batted_balls
                })

    print(f"Extracted logs for {len(pitcher_raw_logs)} pitchers, {len(batter_raw_logs)} batters.")

    # 3. Compute Rolling-Window Metrics & Empirical MFI
    WINDOW = 7  # Rolling 7-game window standard in Sabermetrics
    updated_count = 0

    for name, p_info in target_players.items():
        is_pitcher = (p_info.get('role_type') == '投手')

        # === PITCHERS ===
        if is_pitcher and name in pitcher_raw_logs and len(pitcher_raw_logs[name]) >= 3:
            logs = pitcher_raw_logs[name]
            logs.sort(key=lambda x: x['full_date'])

            valid_vels = [x['avg_ff'] for x in logs if x['avg_ff'] is not None]
            base_vel = float(np.percentile(valid_vels, 80)) if len(valid_vels) >= 3 else 145.0

            valid_disps = [x['disp_cm'] for x in logs if x['disp_cm'] is not None]
            base_disp = float(np.percentile(valid_disps, 25)) if len(valid_disps) >= 3 else 2.1

            cum_er = 0
            cum_outs = 0

            games_idx = []
            dates = []
            mfis = []
            m1s = [] # 釋球點離散 (cm)
            m2s = [] # 速球均速 (km/h)
            m3s = [] # 垂直位移 proxy (in)
            perfs = [] # Cumulative ERA

            # Rolling smoothing for relief pitchers
            for i, entry in enumerate(logs):
                games_idx.append(i + 1)
                dates.append(entry['date'])

                cum_er += entry['er']
                cum_outs += entry['ip_outs']
                era = round((cum_er * 27.0 / cum_outs), 2) if cum_outs > 0 else 0.0
                perfs.append(era)

                # Velocity with rolling fallback
                cur_vel = entry['avg_ff']
                if cur_vel is None:
                    # lookback window
                    sub_vels = [x['avg_ff'] for x in logs[max(0, i-3):i+1] if x['avg_ff'] is not None]
                    cur_vel = float(np.mean(sub_vels)) if sub_vels else base_vel
                m2s.append(round(cur_vel, 1))

                # Dispersion
                cur_disp = entry['disp_cm']
                if cur_disp is None:
                    sub_disps = [x['disp_cm'] for x in logs[max(0, i-3):i+1] if x['disp_cm'] is not None]
                    cur_disp = float(np.mean(sub_disps)) if sub_disps else base_disp
                m1s.append(round(cur_disp, 2))

                # Movement proxy
                cur_mov = entry['vert_mov'] if entry['vert_mov'] is not None else 15.2
                m3s.append(round(cur_mov, 1))

                # 14-day rolling pitch count
                cur_dt = datetime.strptime(entry['full_date'], '%Y-%m-%d')
                rolling_np = sum(
                    x['np'] for x in logs[:i+1]
                    if 0 <= (cur_dt - datetime.strptime(x['full_date'], '%Y-%m-%d')).days <= 14
                )

                vel_drop = max(0.0, base_vel - cur_vel)
                disp_growth = max(0.0, cur_disp - base_disp)
                workload_score = min(25.0, (rolling_np / 160.0) * 20.0)

                mfi = 38.0 + (vel_drop * 4.8) + (disp_growth * 7.5) + workload_score
                mfi = max(24.0, min(88.5, mfi))
                mfis.append(round(mfi, 1))

            p_info['games'] = games_idx
            p_info['dates'] = dates
            p_info['mfi'] = mfis
            p_info['m1'] = m1s
            p_info['m2'] = m2s
            p_info['m3'] = m3s
            p_info['perf'] = perfs
            p_info['data_source'] = "rebas.tw Open Data (CPBL 2024)"
            updated_count += 1

        # === BATTERS (Rolling 7-game calculation) ===
        elif (not is_pitcher) and name in batter_raw_logs and len(batter_raw_logs[name]) >= 3:
            logs = batter_raw_logs[name]
            logs.sort(key=lambda x: x['full_date'])

            total_h = 0
            total_ab = 0

            games_idx = []
            dates = []
            mfis = []
            m1s = [] # 壞球追打率 (O-Swing%) - 7-game rolling
            m2s = [] # 帶內揮空率 (Z-Whiff%) - 7-game rolling
            m3s = [] # 強擊球率 (HardHit%) - 7-game rolling
            perfs = [] # Cumulative AVG

            # First compute rolling series
            raw_oswings = []
            raw_zwhiffs = []
            raw_hardhits = []

            for i in range(len(logs)):
                start = max(0, i - WINDOW + 1)
                sub = logs[start:i+1]

                sum_op = sum(x['o_pitches'] for x in sub)
                sum_os = sum(x['o_swings'] for x in sub)
                oswing = (sum_os / sum_op * 100.0) if sum_op >= 5 else None

                sum_zs = sum(x['z_swings'] for x in sub)
                sum_zw = sum(x['z_whiffs'] for x in sub)
                zwhiff = (sum_zw / sum_zs * 100.0) if sum_zs >= 4 else None

                sum_hh = sum(x['hard_hits'] for x in sub)
                sum_bb = sum(x['batted_balls'] for x in sub)
                hardhit = (sum_hh / sum_bb * 100.0) if sum_bb >= 3 else None

                raw_oswings.append(oswing)
                raw_zwhiffs.append(zwhiff)
                raw_hardhits.append(hardhit)

            # Determine player's career baseline from valid entries
            valid_os = [v for v in raw_oswings if v is not None]
            base_os = float(np.percentile(valid_os, 30)) if len(valid_os) >= 3 else 28.5

            valid_zw = [v for v in raw_zwhiffs if v is not None]
            base_zw = float(np.percentile(valid_zw, 30)) if len(valid_zw) >= 3 else 10.5

            valid_hh = [v for v in raw_hardhits if v is not None]
            base_hh = float(np.percentile(valid_hh, 70)) if len(valid_hh) >= 3 else 36.0

            for i, entry in enumerate(logs):
                games_idx.append(i + 1)
                dates.append(entry['date'])

                total_h += entry['h']
                total_ab += entry['ab']
                avg = round(total_h / total_ab, 3) if total_ab > 0 else 0.250
                perfs.append(avg)

                # Get smoothed metrics
                cur_os = raw_oswings[i] if raw_oswings[i] is not None else base_os
                cur_zw = raw_zwhiffs[i] if raw_zwhiffs[i] is not None else base_zw
                cur_hh = raw_hardhits[i] if raw_hardhits[i] is not None else base_hh

                # Natural variance check: ensure realistic non-zero ranges
                cur_os = max(14.0, min(58.0, cur_os))
                cur_zw = max(4.5, min(38.0, cur_zw))
                cur_hh = max(12.0, min(65.0, cur_hh))

                m1s.append(round(cur_os, 1))
                m2s.append(round(cur_zw, 1))
                m3s.append(round(cur_hh, 1))

                # Fatigue formulation
                cur_dt = datetime.strptime(entry['full_date'], '%Y-%m-%d')
                games_14d = sum(
                    1 for x in logs[:i+1]
                    if 0 <= (cur_dt - datetime.strptime(x['full_date'], '%Y-%m-%d')).days <= 14
                )

                oswing_diff = max(0.0, cur_os - base_os)
                zwhiff_diff = max(0.0, cur_zw - base_zw)
                hardhit_drop = max(0.0, base_hh - cur_hh)
                workload_score = min(20.0, (games_14d / 10.0) * 16.0)

                mfi = 38.0 + (oswing_diff * 0.95) + (zwhiff_diff * 1.35) + (hardhit_drop * 0.45) + workload_score
                mfi = max(24.0, min(86.5, mfi))
                mfis.append(round(mfi, 1))

            p_info['games'] = games_idx
            p_info['dates'] = dates
            p_info['mfi'] = mfis
            p_info['m1'] = m1s
            p_info['m2'] = m2s
            p_info['m3'] = m3s
            p_info['perf'] = perfs
            p_info['data_source'] = "rebas.tw Open Data (CPBL 2024)"
            updated_count += 1

    print(f"Successfully processed rolling metrics for {updated_count} players!")

    # 4. Save updated files
    with open('players_data.json', 'w', encoding='utf-8') as f:
        json.dump(target_players, f, ensure_ascii=False, indent=2)

    js_code = f"window.PLAYERS_DATA = {json.dumps(target_players, ensure_ascii=False)};"
    with open('players_data.js', 'w', encoding='utf-8') as f:
        f.write(js_code)

    print("players_data.json and players_data.js updated!")

if __name__ == '__main__':
    main()
