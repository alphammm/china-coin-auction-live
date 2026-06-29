# 中国古钱币 · 实时拍卖聚合 (China Coin Auction Live)

聚合全球主要拍卖平台**正在进行 / 即将截止**的中国古钱与机制币专场，
关键词一键直达各平台的**已筛选实时列表**，并附海外寄拍平台目录。

**本地路径**：`~/Desktop/Claude Code/China-Coin-Auction-Live/`
**数据时点**：2026-06-29

---

## 一句话原理

纯前端无法逐秒抓取各拍卖行私有库存（反爬 + CORS）。本站采用：

- **策展面板**：人工维护的当前现役专场卡片 + 实时倒计时
- **一键直达**：关键词按钮实时跳转到 NumisBids / Biddr / Heritage / Stephen Album / GreatCollections / Google 的官方筛选结果页（数据以平台为准）

---

## 功能

| 区块 | 说明 |
|------|------|
| 现役拍卖面板 | 专场卡片，LIVE / 即将开始 / 寄拍截止 三态，逐秒倒计时 |
| 一键直达检索 | 选平台 → 点关键词（按朝代/品类分组）→ 打开实时筛选页；支持自定义词 |
| 全球平台目录 | 11 家拍卖行/平台，含地区、定位、是否接受海外寄拍、适合品类、官网直达 |
| 实时时钟 | 顶部本地时间 + 日期，每秒刷新 |

---

## 维护方式（无需懂代码）

打开 `index.html`，编辑顶部三个 JS 数组即可：

- **`AS_OF`** — 数据时点字符串
- **`AUCTIONS`** — 增删拍卖卡片。字段：
  - `status`：`"live"`（进行中）/ `"soon"`（即将开始）/ `"consign"`（寄拍征集）
  - `end`：ISO 截止时间（带时区），倒计时目标
  - `house / title / desc / tags / link`
- **`PLATFORMS`** — 平台搜索链接模板（`{q}` 自动替换为编码关键词）
- **`KW_GROUPS`** — 关键词，格式 `["中文显示","实际检索英文term"]`

改完直接刷新浏览器即可，无需构建。

---

## 已收录平台搜索链接格式

| 平台 | 模板 |
|------|------|
| NumisBids | `numisbids.com/n.php?p=searchall&searchall={q}` |
| Biddr | `biddr.com/search?q={q}` |
| Heritage | `coins.ha.com/c/search-results.zx?Ntt={q}` |
| Stephen Album | `sarc.auction/?searchword={q}` |
| GreatCollections | `greatcollections.com/search.php?q={q}` |

---

## 部署（可选）

纯静态单文件，可直接拖到 Vercel / Netlify，或 `git push` 自动部署。

```bash
cd ~/Desktop/Claude\ Code/China-Coin-Auction-Live
# git init && git add . && git commit -m "init" && 推送到 GitHub
```

---

## 后续可扩展

- 后端爬虫 / 各平台 API → 真正逐秒抓取在拍 lot（需服务器）
- Telegram / 邮件提醒：某关键词出现新 lot 时推送
- 历史成交价数据库（参考 1024-Collection 的 localStorage 方案）
