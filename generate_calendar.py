import requests
import json
from icalendar import Calendar, Event
from datetime import datetime, timezone, timedelta
import os

# --- 配置信息 ---
# 从你抓包中获取的接口URL
API_URL = "https://kplshop-op.timi-esports.qq.com/kplow/getScheduleList"
# 请求头，模拟浏览器行为，关键是要带上 referer 和 origin
HEADERS = {
    "Content-Type": "application/json",
    "Referer": "http://kpl.qq.com/",
    "Origin": "http://kpl.qq.com",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36 Edg/149.0.0.0",
    "Accept": "application/json, text/plain, */*",
}
# 请求体，根据你抓包的数据，这里是获取常规赛第一轮
PAYLOAD = {"stageid": "cgs1"}

# 中国时区 (UTC+8)
CHINA_TZ = timezone(timedelta(hours=8))

def fetch_season_info():
    """获取当前赛季名称"""
    try:
        # 使用你抓包到的接口
        season_api = "https://kplshop-op.timi-esports.qq.com/kplow/getSeasonAndStageAndTeamList"
        headers = {
            "Content-Type": "application/json",
            "Referer": "http://kpl.qq.com/",
            "Origin": "http://kpl.qq.com",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json, text/plain, */*",
        }
        payload = {}  # 根据你的抓包，这个接口的请求体可能是空的或只有空对象
        
        response = requests.post(season_api, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get('result') == 0:
            seasons = data.get('data', {}).get('seasons', [])
            # 找到当前赛季（is_cur_season == 1）
            for season in seasons:
                if season.get('is_cur_season') == 1:
                    return season.get('season_name', 'KPL')
            # 如果没找到当前赛季，返回第一个
            if seasons:
                return seasons[0].get('season_name', 'KPL')
        return 'KPL'
    except Exception as e:
        print(f"⚠️ 获取赛季信息失败: {e}")
        return 'KPL'
    
def fetch_schedule():
    """从API获取赛程数据"""
    try:
        response = requests.post(API_URL, headers=HEADERS, json=PAYLOAD, timeout=10)
        response.raise_for_status()  # 如果状态码不是200，抛出异常
        data = response.json()
        if data.get('result') == 0:
            return data.get('data', {}).get('list', [])
        else:
            print(f"API返回错误: {data.get('msg')}")
            return []
    except requests.exceptions.RequestException as e:
        print(f"请求API失败: {e}")
        return []

def create_calendar(matches, calendar_title=None):
    """创建并返回一个ics日历对象"""
    cal = Calendar()
    cal.add('prodid', '-//KPL Schedule//kpl.qq.com//')
    cal.add('version', '2.0')
    cal.add('calscale', 'GREGORIAN')
    
    # 使用动态标题
    if calendar_title:
        cal.add('x-wr-calname', calendar_title)
    else:
        cal.add('x-wr-calname', 'KPL王者荣耀职业联赛赛程')
    
    cal.add('x-wr-timezone', 'Asia/Shanghai')

    for match in matches:
        # 提取数据
        start_ts = int(match.get('start_timestamp', 0))
        if start_ts == 0:
            continue  # 没有时间则跳过

        team_a = match.get('team_a_name', '队伍A')
        team_b = match.get('team_b_name', '队伍B')
        stage = match.get('stage_name', 'KPL')
        # 构建事件标题，例如: "KPL 常规赛第一轮: 佛山DRG vs 广州TTG"
        summary = f"{stage}: {team_a} vs {team_b}"
        location = match.get('location_name', '')
        # 比分信息可以作为描述添加
        score_a = match.get('team_a_score', '')
        score_b = match.get('team_b_score', '')
        description = f"BO{match.get('bo_total', 5)}"
        if score_a != '' and score_b != '':
            description += f" | 比分: {team_a} {score_a} - {score_b} {team_b}"

        # 创建事件
        event = Event()
        # 将Unix时间戳转换为datetime对象，并设置为中国时区
        # 注意：start_timestamp 是字符串，需要先转为int
        start_time = datetime.fromtimestamp(start_ts, tz=CHINA_TZ)
        # 简单估算结束时间：BO5大约3小时，可以根据需要调整
        end_time = start_time + timedelta(hours=2)

        event.add('summary', summary)
        event.add('dtstart', start_time)
        event.add('dtend', end_time)
        event.add('dtstamp', datetime.now(timezone.utc))
        if location:
            event.add('location', location)
        if description:
            event.add('description', description)
        # 添加一个唯一的UID，用于日历去重
        uid = match.get('scheduleid', f"{start_ts}_{team_a}_{team_b}")
        event.add('uid', uid)
        # 设置事件的时区为透明，以便在不同时区显示正确时间
        event.add('transp', 'OPAQUE')

        cal.add_component(event)

    return cal

def save_calendar(cal, filename="kpl.ics"):
    """将日历对象保存为文件"""
    with open(filename, 'wb') as f:
        f.write(cal.to_ical())
    print(f"✅ 日历文件已生成: {filename}")

def main():
    print("🚀 开始获取KPL赛程...")
    
    # 先获取赛季名称
    season_name = fetch_season_info()
    print(f"📌 当前赛季: {season_name}")
    
    # 获取赛程数据
    matches = fetch_schedule()
    if not matches:
        print("⚠️ 未能获取到任何赛程数据，请检查网络或接口状态。")
        return

    print(f"✅ 成功获取 {len(matches)} 场比赛。")
    
    # 获取阶段名称
    stage_name = matches[0].get('stage_name', 'KPL') if matches else 'KPL'
    full_title = f"{season_name} {stage_name}"
    print(f"📅 日历标题: {full_title}")
    
    # 生成 ics 日历
    print("📅 正在生成日历文件...")
    cal = create_calendar(matches, full_title)
    save_calendar(cal)
    
    # 生成 JSON 数据供前端展示
    print("📊 正在生成赛程数据...")
    matches_data = []
    current_ts = int(time.time())
    
    for match in matches:
        start_ts = int(match.get('start_timestamp', 0))
        if start_ts == 0:
            continue
        start_time = datetime.fromtimestamp(start_ts, tz=CHINA_TZ)
        
        score_a_raw = match.get('team_a_score')
        score_b_raw = match.get('team_b_score')
        bo_total = match.get('bo_total', 5)  # 默认 BO5
        
        # 判断是否有比分数据
        has_score = (
            score_a_raw is not None and score_a_raw != '' and
            score_b_raw is not None and score_b_raw != ''
        )
        
        # ✅ 新的状态判断逻辑
        is_finished = False
        is_live = False
        
        if has_score:
            score_a = int(score_a_raw)
            score_b = int(score_b_raw)
            
            # 判断是否已结束：一边达到胜利分数
            # BO5: 一方达到3分；BO7: 一方达到4分；BO9: 一方达到5分
            win_score = (bo_total // 2) + 1  # BO5->3, BO7->4, BO9->5
            if score_a >= win_score or score_b >= win_score:
                is_finished = True
            # 判断是否正在进行：有比分但未结束，且比赛开始时间已过
            elif current_ts > start_ts:
                is_live = True
            # 两边都是0，且比赛还没开始
            elif score_a == 0 and score_b == 0 and current_ts < start_ts:
                is_finished = False
                is_live = False
        else:
            # 没有比分数据，视为未开始
            is_finished = False
            is_live = False
        
        # 比分值
        if is_finished:
            score_a_display = str(score_a_raw)
            score_b_display = str(score_b_raw)
        else:
            score_a_display = None
            score_b_display = None
        
        # 状态文本
        if is_finished:
            status = 'finished'
        elif is_live:
            status = 'live'
        else:
            status = 'upcoming'
        
        matches_data.append({
            'time': start_time.strftime('%m-%d %H:%M'),
            'weekday': ['周一','周二','周三','周四','周五','周六','周日'][start_time.weekday()],
            'team_a': match.get('team_a_name', ''),
            'team_a_logo': match.get('team_a_logo', ''),
            'team_b': match.get('team_b_name', ''),
            'team_b_logo': match.get('team_b_logo', ''),
            'stage': match.get('stage_name', ''),
            'location': match.get('location_name', ''),
            'score_a': score_a_display,
            'score_b': score_b_display,
            'is_finished': is_finished,
            'is_live': is_live,
            'status': status,
            'bo_total': bo_total
        })
    
    output_data = {
        'title': full_title,
        'season': season_name,
        'stage': stage_name,
        'matches': matches_data
    }
    
    with open('schedule.json', 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    print("✅ 赛程数据已保存: schedule.json")
    
    print("🎉 任务完成！")
    
if __name__ == "__main__":
    main()