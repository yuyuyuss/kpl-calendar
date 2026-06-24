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

def create_calendar(matches):
    """创建并返回一个ics日历对象"""
    cal = Calendar()
    cal.add('prodid', '-//KPL Schedule//kpl.qq.com//')
    cal.add('version', '2.0')
    cal.add('calscale', 'GREGORIAN')
    # 日历标题
    cal.add('x-wr-calname', 'KPL王者荣耀职业联赛赛程')
    # 让日历默认显示为亚洲/上海时区
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
        end_time = start_time + timedelta(hours=3)

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
    matches = fetch_schedule()
    if not matches:
        print("⚠️ 未能获取到任何赛程数据，请检查网络或接口状态。")
        return

    print(f"✅ 成功获取 {len(matches)} 场比赛。")
    
    # 生成 ics 日历
    print("📅 正在生成日历文件...")
    cal = create_calendar(matches)
    save_calendar(cal)
    
    # 🆕 生成 JSON 数据供前端展示
    print("📊 正在生成赛程数据...")
    matches_data = []
    for match in matches:
        start_ts = int(match.get('start_timestamp', 0))
        if start_ts == 0:
            continue
        start_time = datetime.fromtimestamp(start_ts, tz=CHINA_TZ)
        matches_data.append({
            'time': start_time.strftime('%m-%d %H:%M'),
            'weekday': ['周一','周二','周三','周四','周五','周六','周日'][start_time.weekday()],
            'team_a': match.get('team_a_name', ''),
            'team_b': match.get('team_b_name', ''),
            'stage': match.get('stage_name', ''),
            'location': match.get('location_name', '')
        })
    
    with open('schedule.json', 'w', encoding='utf-8') as f:
        json.dump(matches_data, f, ensure_ascii=False, indent=2)
    print("✅ 赛程数据已保存: schedule.json")
    
    print("🎉 任务完成！")

if __name__ == "__main__":
    main()