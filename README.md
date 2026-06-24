# 📅 KPL 赛程日历订阅

> 自动抓取 KPL（王者荣耀职业联赛）赛程数据，生成可订阅的日历链接，支持一键更新。

[![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-自动更新-blue)](https://github.com/yuyuyuss/kpl-calendar/actions)
[![GitHub Pages](https://img.shields.io/badge/GitHub%20Pages-在线预览-brightgreen)](https://yuyuyuss.github.io/kpl-calendar/)
[![License](https://img.shields.io/badge/License-MIT-orange)](LICENSE)

---

## ✨ 功能特点

- 📊 **赛程展示** — 网页清晰展示所有赛程，含战队队标、实时比分
- 🏷️ **智能状态** — 自动区分「未开始 · 进行中 · 已结束」三种状态
- 📅 **日历订阅** — 生成标准 `.ics` 日历文件，支持 Apple / Google / Outlook 日历
- 🔄 **一键更新** — 通过 GitHub Actions 手动触发，随时抓取最新赛程
- 🖼️ **战队 LOGO** — 自动显示战队图标，视觉更直观

---

## 🚀 快速开始

### 1️⃣ 在线查看赛程

访问 👉 **[https://yuyuyuss.github.io/kpl-calendar/](https://yuyuyuss.github.io/kpl-calendar/)**

### 2️⃣ 订阅日历

复制下方链接，在日历 App 中添加订阅：

```
webcal://yuyuyuss.github.io/kpl-calendar/kpl.ics
```

**各平台添加方式：**

| 平台 | 操作 |
|------|------|
| 🍎 iPhone / iPad | 「设置」→「日历」→「账户」→「添加账户」→「其他」→「添加已订阅的日历」|
| 📧 Google 日历 | 左侧「其他日历」旁的「+」→「通过网址添加」|
| 💻 Outlook | 「添加日历」→「从 Internet 订阅」|

### 3️⃣ 手动更新赛程

当赛程有变动时，点击页面上的 **「前往 GitHub 更新赛程」** 按钮，或直接进入 [Actions 页面](https://github.com/yuyuyuss/kpl-calendar/actions/workflows/update-calendar.yml)，点击绿色的 **「Run workflow」** 即可。

---

## 🛠️ 技术架构

| 组件 | 技术 |
|------|------|
| 🐍 数据抓取 | Python + Requests |
| 📅 日历生成 | Python + icalendar |
| ⚙️ 自动化部署 | GitHub Actions |
| 🎨 前端展示 | 原生 HTML + CSS + JavaScript |
| 🌐 页面托管 | GitHub Pages |

### 数据流程图

```
KPL 官方 API
      ↓
Python 脚本 (generate_calendar.py)
      ↓
┌─────────────┴─────────────┐
↓                           ↓
kpl.ics (日历文件)    schedule.json (赛程数据)
↓                           ↓
GitHub Pages 部署 ───→ 前端页面展示
      ↓
用户订阅日历 / 在线查看
```

---

## 📂 项目结构

```
kpl-calendar/
├── .github/
│   └── workflows/
│       └── update-calendar.yml   # GitHub Actions 自动化配置
├── generate_calendar.py          # 核心脚本：抓取数据 + 生成日历
├── index.html                    # 前端展示页面
├── kpl.ics                       # 生成的日历文件
├── schedule.json                 # 生成的赛程数据
├── requirements.txt              # Python 依赖列表
└── README.md                     # 项目说明
```

---

## 📊 数据来源

赛程数据来自 KPL 官方接口：

| 接口 | 用途 |
|------|------|
| `getScheduleList` | 获取赛程列表（含比分、队标、时间等）|
| `getSeasonAndStageAndTeamList` | 获取赛季名称和阶段信息 |

---

## 🔧 本地开发

### 环境要求

- Python 3.11+
- Git

### 克隆项目

```bash
git clone https://github.com/yuyuyuss/kpl-calendar.git
cd kpl-calendar
```

### 安装依赖

```bash
pip install -r requirements.txt
```

### 本地运行

```bash
python generate_calendar.py
```

运行后会在项目根目录生成 `kpl.ics` 和 `schedule.json` 文件。

---

## 🔐 安全说明

- ✅ 公开仓库，所有代码开源
- ✅ 使用 `workflow_dispatch` 手动触发，无需 Token
- ✅ 不存储任何用户数据
- ✅ 所有请求仅涉及公开的 KPL 官方 API

---

## 📌 注意事项

- 赛程数据由 KPL 官方提供，本工具仅做整合展示，数据准确性依赖官方接口
- 日历订阅需使用 `webcal://` 协议添加
- 建议每周手动更新一次赛程，确保数据为最新
- 如果队标图片无法显示，可能是网络问题，不影响核心功能

---

## 🤝 贡献

欢迎提交 Issue 或 Pull Request！

1. Fork 本仓库
2. 创建你的功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

---

## 📄 许可证

MIT License © 2026 yuyuyuss

---

**🎮 祝你观赛愉快！KPL 赛场见！** 🏆
