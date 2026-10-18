import requests
import json
import time
from icalendar import Calendar, Event
from datetime import datetime, timezone, timedelta

# --- 接口配置 ---
API_SCHEDULE = "https://kplshop-op.timi-esports.qq.com/kplow/getScheduleList"

HEADERS = {
    "Content-Type": "application/json",
    "Referer": "http://kpl.qq.com/",
    "Origin": "http://kpl.qq.com",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36 Edg/149.0.0.0",
    "Accept": "application/json, text/plain, */*",
}
CHINA_TZ = timezone(timedelta(hours=8))

# 详情接口已经404，直接关闭
FETCH_DETAIL = False


def get_current_season():
    """拿到当前赛季名称 + seasonid"""
    url = "https://kplshop-op.timi-esports.qq.com/kplow/getSeasonAndStageAndTeamList"
    resp = requests.post(url, headers=HEADERS, json={}, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    if data["result"] != 0:
        raise Exception("获取赛季失败")
    for s in data["data"]["seasons"]:
        if s["is_cur_season"] == 1:
            return s["season_name"], s["seasonid"]
    raise Exception("未找到当前赛季")


def discover_all_stages(seed_stage_ids):
    """
    多种子stage拉取，合并赛程后自动提取全部stage
    支持后续突围赛、淘汰赛上新自动识别
    """
    all_raw_matches = []
    for seed in seed_stage_ids:
        print(f"\n🔍 种子stage[{seed}]拉取赛程，用于自动发现阶段...")
        resp = requests.post(API_SCHEDULE, headers=HEADERS, json={"stageid": seed}, timeout=10)
        resp.raise_for_status()
        j = resp.json()
        if j["result"] != 0:
            print(f"⚠️ 种子 {seed} 请求失败，跳过")
            continue
        match_list = j["data"]["list"]
        all_raw_matches.extend(match_list)

    stage_map = {}
    for m in all_raw_matches:
        sid = m["stageid"]
        sname = m["stage_name"]
        stage_map[sid] = sname

    stage_list = [{"stageid": k, "stage_name": v} for k, v in stage_map.items()]
    print(f"✅ 自动识别到本赛季阶段列表：{stage_list}")
    return stage_list


def fetch_one_stage(stage):
    sid = stage["stageid"]
    sname = stage["stage_name"]
    print(f"\n📥 抓取【{sname}】stageid={sid}")
    resp = requests.post(API_SCHEDULE, headers=HEADERS, json={"stageid": sid}, timeout=10)
    resp.raise_for_status()
    j = resp.json()
    if j["result"] != 0:
        print(f"⚠️ 【{sname}】返回错误：{j.get('msg')}")
        return []
    matches = j["data"]["list"]
    print(f"✅ 【{sname}】拿到 {len(matches)} 场比赛")
    return matches


def build_ical(all_matches, title):
    cal = Calendar()
    cal.add('prodid', '-//KPL Auto Schedule Crawler//kpl.qq.com//')
    cal.add('version', '2.0')
    cal.add('calscale', 'GREGORIAN')
    cal.add('x-wr-calname', title)
    cal.add('x-wr-timezone', 'Asia/Shanghai')

    for m in all_matches:
        ts = int(m["start_timestamp"])
        if ts <= 0:
            continue
        ta = m["team_a_name"]
        tb = m["team_b_name"]
        summary = f"{ta} vs {tb}"
        loc = m.get("location_name", "")
        sa = m.get("team_a_score", "")
        sb = m.get("team_b_score", "")
        bo = m["bo_total"]
        stg = m["stage_name"]
        desc = f"【{stg}】BO{bo}"
        if sa != "" and sb != "":
            desc += f" | 比分 {ta} {sa}-{sb} {tb}"

        evt = Event()
        st = datetime.fromtimestamp(ts, tz=CHINA_TZ)
        et = st + timedelta(hours=2)
        evt.add("summary", summary)
        evt.add("dtstart", st)
        evt.add("dtend", et)
        evt.add("dtstamp", datetime.now(timezone.utc))
        if loc:
            evt.add("location", loc)
        evt.add("description", desc)
        evt.add("uid", m["scheduleid"])
        cal.add_component(evt)
    return cal


def main():
    print("🚀 KPL自动抓取脚本（自动发现全部stage，无需硬编码新增）")
    season_name, seasonid = get_current_season()
    print(f"📌 当前赛季：{season_name} | seasonid={seasonid}")

    # 多种子，同时扫描擂台赛、总决赛，后续上新阶段会自动识别
    seed_list = ["lts", "zjs"]
    all_stages = discover_all_stages(seed_list)

    all_matches = []
    seen_sid = set()
    for stg in all_stages:
        ms = fetch_one_stage(stg)
        for m in ms:
            if m["scheduleid"] not in seen_sid:
                seen_sid.add(m["scheduleid"])
                all_matches.append(m)

    if not all_matches:
        print("❌ 没有抓到任何赛程")
        return

    # 生成ics日历文件
    cal = build_ical(all_matches, season_name)
    with open("kpl.ics", "wb") as f:
        f.write(cal.to_ical())
    print("\n✅ kpl.ics 已生成")

    # 组装json
    out_items = []
    for m in all_matches:
        ts = int(m["start_timestamp"])
        dt = datetime.fromtimestamp(ts, tz=CHINA_TZ)
        sid = m["scheduleid"]
        sa_raw = m.get("team_a_score")
        sb_raw = m.get("team_b_score")
        bo = m["bo_total"]
        stg_name = m["stage_name"]

        is_finished = False
        score_a = None
        score_b = None
        if sa_raw not in (None, "") and sb_raw not in (None, ""):
            try:
                sa = int(sa_raw)
                sb = int(sb_raw)
                win_line = (bo // 2) + 1
                if sa >= win_line or sb >= win_line:
                    is_finished = True
                    score_a = str(sa)
                    score_b = str(sb)
            except:
                pass

        item = {
            "scheduleid": sid,
            "time": dt.strftime("%m-%d %H:%M"),
            "weekday": ["周一","周二","周三","周四","周五","周六","周日"][dt.weekday()],
            "team_a": m["team_a_name"],
            "team_a_logo": m.get("team_a_logo"),
            "team_b": m["team_b_name"],
            "team_b_logo": m.get("team_b_logo"),
            "stage": stg_name,
            "location": m.get("location_name"),
            "score_a": score_a,
            "score_b": score_b,
            "is_finished": is_finished
        }
        out_items.append(item)

    final_json = {
        "title": season_name,
        "seasonid": seasonid,
        "stages": all_stages,
        "matches": out_items
    }
    with open("schedule.json", "w", encoding="utf-8") as f:
        json.dump(final_json, f, ensure_ascii=False, indent=2)
    print("✅ schedule.json 已生成")
    print("\n🎉 全部完成！突围赛/淘汰赛上线后，直接重新运行脚本自动抓取")


if __name__ == "__main__":
    main()
