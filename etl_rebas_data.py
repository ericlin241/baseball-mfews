"""
ETL Pipeline: Integrate rebas.tw Open Data into MFEWS (Micro-Fatigue Early Warning System)
Source: https://github.com/rebas-tw/rebas.tw-open-data (ODC-By License)
Dataset: CPBL-2024-OpenData (360 Games, Full Pitch-by-Pitch Tracking)
"""

import zipfile
import json
import math
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
    print("=== [MFEWS ETL] Processing rebas.tw Open Data (CPBL 2024) ===")
    
    # 1. Load template players_data.json
    with open('players_data.json', 'r', encoding='utf-8') as f:
        target_players = json.load(f)
    print(f"Loaded {len(target_players)} target players in database.")

    # 2. Extract and organize all 360 games from cpbl_2024.zip
    pitcher_raw_logs = defaultdict(list)
    batter_raw_logs = defaultdict(list)

    with zipfile.ZipFile('cpbl_2024.zip', 'r') as z:
        game_files = [n for n in z.namelist() if n.endswith('.json') and 'G' in n]
        print(f"Found {len(game_files)} game JSONs in cpbl_2024.zip. Parsing...")

        # Sort files by game number
        def get_gnum(name):
            try:
                base = name.split('/')[-1].replace('.json', '')
                num = int(base.split('-G')[-1])
                return num
            except Exception:
                return 9999
        game_files.sort(key=get_gnum)

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

            # Collect plate appearances by pitcher and batter
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

            # Process Pitchers
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
                # coordinate dispersion in cm (normalized std)
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

            # Process Batters
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

                # O-Swing: swings at balls
                o_swings = sum(1 for ev in pitches if ev.get('isBall') and ev.get('pitchCode') in ['SW', 'F', 'FT', 'H', 'TRY_BUNT', 'FOUL_BUNT'])
                o_pitches = sum(1 for ev in pitches if ev.get('isBall'))
                o_swing_pct = (o_swings / o_pitches * 100) if o_pitches >= 3 else None

                # Z-Whiff: whiffs at strikes
                z_whiffs = sum(1 for ev in pitches if ev.get('isStrike') and ev.get('pitchCode') in ['SW', 'TRY_BUNT'])
                z_swings = sum(1 for ev in pitches if ev.get('isStrike') and ev.get('pitchCode') in ['SW', 'F', 'FT', 'H', 'TRY_BUNT', 'FOUL_BUNT'])
                z_whiff_pct = (z_whiffs / z_swings * 100) if z_swings >= 2 else None

                # Hard hits
                hard_hits = sum(1 for pa in pas if pa.get('hardness') == 'HARD')
                total_hits_in_play = sum(1 for pa in pas if pa.get('hardness') in ['HARD', 'MED', 'SOFT'])
                hard_hit_pct = (hard_hits / total_hits_in_play * 100) if total_hits_in_play > 0 else None

                batter_raw_logs[b_name].append({
                    'date': mm_dd,
                    'full_date': g_date,
                    'pa': int(b.get('PA', 0)),
                    'ab': int(b.get('AB', 0)),
                    'h': int(b.get('H', 0)),
                    'bb': int(b.get('BB', 0)),
                    'so': int(b.get('SO', 0)),
                    'hr': int(b.get('HR', 0)),
                    'o_swing': o_swing_pct,
                    'z_whiff': z_whiff_pct,
                    'hard_hit': hard_hit_pct
                })

    print(f"Extracted logs: {len(pitcher_raw_logs)} pitchers, {len(batter_raw_logs)} batters.")

    # 3. Process Each Target Player with MFEWS Biomechanical Micro-Fatigue Formulation
    updated_count = 0

    for name, p_info in target_players.items():
        is_pitcher = (p_info.get('role_type') == '投手')
        
        if is_pitcher and name in pitcher_raw_logs and len(pitcher_raw_logs[name]) >= 3:
            logs = pitcher_raw_logs[name]
            logs.sort(key=lambda x: x['full_date'])

            # Baseline calculation for pitcher
            valid_vels = [x['avg_ff'] for x in logs if x['avg_ff'] is not None]
            base_vel = float(np.percentile(valid_vels, 85)) if len(valid_vels) >= 3 else (valid_vels[0] if valid_vels else 145.0)

            valid_disps = [x['disp_cm'] for x in logs if x['disp_cm'] is not None]
            base_disp = float(np.percentile(valid_disps, 20)) if len(valid_disps) >= 3 else 2.1

            cum_er = 0
            cum_outs = 0

            games_idx = []
            dates = []
            mfis = []
            m1s = [] # 釋球點離散 (cm)
            m2s = [] # 速球均速 (km/h)
            m3s = [] # 垂直位移 proxy (in)
            perfs = [] # Cumulative ERA

            for i, entry in enumerate(logs):
                games_idx.append(i + 1)
                dates.append(entry['date'])

                # ERA calculation
                cum_er += entry['er']
                cum_outs += entry['ip_outs']
                era = round((cum_er * 27.0 / cum_outs), 2) if cum_outs > 0 else 0.0
                perfs.append(era)

                # Velocity
                cur_vel = entry['avg_ff'] if entry['avg_ff'] is not None else base_vel
                m2s.append(round(cur_vel, 1))

                # Dispersion
                cur_disp = entry['disp_cm'] if entry['disp_cm'] is not None else base_disp
                m1s.append(round(cur_disp, 2))

                # Movement proxy
                cur_mov = entry['vert_mov'] if entry['vert_mov'] is not None else 15.0
                m3s.append(round(cur_mov, 1))

                # 14-day rolling pitch count
                cur_dt = datetime.strptime(entry['full_date'], '%Y-%m-%d')
                rolling_np = sum(
                    x['np'] for x in logs[:i+1]
                    if 0 <= (cur_dt - datetime.strptime(x['full_date'], '%Y-%m-%d')).days <= 14
                )

                # MFI Formulation (Physics & Biomechanics grounded)
                # Normal baseline = 42
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

        elif (not is_pitcher) and name in batter_raw_logs and len(batter_raw_logs[name]) >= 3:
            logs = batter_raw_logs[name]
            logs.sort(key=lambda x: x['full_date'])

            # Baseline calculation for batter
            valid_oswings = [x['o_swing'] for x in logs if x['o_swing'] is not None]
            base_oswing = float(np.percentile(valid_oswings, 25)) if len(valid_oswings) >= 3 else 28.0

            valid_zwhiffs = [x['z_whiff'] for x in logs if x['z_whiff'] is not None]
            base_zwhiff = float(np.percentile(valid_zwhiffs, 25)) if len(valid_zwhiffs) >= 3 else 12.0

            cum_h = 0
            cum_ab = 0

            games_idx = []
            dates = []
            mfis = []
            m1s = [] # 壞球追打率 (O-Swing%)
            m2s = [] # 帶內揮空率 (Z-Whiff%)
            m3s = [] # 強擊球率 (HardHit%)
            perfs = [] # Cumulative AVG

            for i, entry in enumerate(logs):
                games_idx.append(i + 1)
                dates.append(entry['date'])

                # Batting AVG calculation
                cum_h += entry['h']
                cum_ab += entry['ab']
                avg = round(cum_h / cum_ab, 3) if cum_ab > 0 else 0.250
                perfs.append(avg)

                # O-Swing%
                cur_oswing = entry['o_swing'] if entry['o_swing'] is not None else base_oswing
                m1s.append(round(cur_oswing, 1))

                # Z-Whiff%
                cur_zwhiff = entry['z_whiff'] if entry['z_whiff'] is not None else base_zwhiff
                m2s.append(round(cur_zwhiff, 1))

                # Hard Hit%
                cur_hard = entry['hard_hit'] if entry['hard_hit'] is not None else 35.0
                m3s.append(round(cur_hard, 1))

                # Consecutive games in 14 days
                cur_dt = datetime.strptime(entry['full_date'], '%Y-%m-%d')
                games_14d = sum(
                    1 for x in logs[:i+1]
                    if 0 <= (cur_dt - datetime.strptime(x['full_date'], '%Y-%m-%d')).days <= 14
                )

                # MFI Formulation (Visual & Cognitive Latency grounded)
                oswing_diff = max(0.0, cur_oswing - base_oswing)
                zwhiff_diff = max(0.0, cur_zwhiff - base_zwhiff)
                workload_score = min(22.0, (games_14d / 10.0) * 18.0)

                mfi = 38.0 + (oswing_diff * 0.95) + (zwhiff_diff * 1.25) + workload_score
                mfi = max(24.0, min(86.0, mfi))
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

    print(f"Directly updated {updated_count} / {len(target_players)} players with authentic REBAS Open Data game logs!")

    # 4. Save updated players_data.json and players_data.js
    with open('players_data.json', 'w', encoding='utf-8') as f:
        json.dump(target_players, f, ensure_ascii=False, indent=2)

    js_code = f"window.PLAYERS_DATA = {json.dumps(target_players, ensure_ascii=False)};"
    with open('players_data.js', 'w', encoding='utf-8') as f:
        f.write(js_code)

    print(f"Generated players_data.json ({len(json.dumps(target_players))} chars)")
    print(f"Generated players_data.js ({len(js_code)} chars)")
    print("ETL execution completed successfully!")

if __name__ == '__main__':
    main()
