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

---

## 🧿 玉器 / 翡翠版：`jade.html`

同一套架构的**中国玉器 · 翡翠拍卖聚合**页面，与古钱版并列（页头可互相切换）。

| 区块 | 说明 |
|------|------|
| 玉器品类图谱 | 12 个可检索品类卡（玉琮/玉璧/红山玉龙/剑饰/带钩/子冈牌/乾隆御题/山子/痕都斯坦/翡翠手镯/帝王绿/羊脂白玉），点击即用该品类的英文专业术语检索 |
| 重点档期面板 | 9 张档期卡。**只有确定日期的条目显示倒计时**（如 2026 秋季亚洲艺术周 9/10–9/18），其余标为"常规档期"并直达官方日历，避免假精确 |
| 一键直达检索 | 8 个平台 × 37 个关键词（高古玉 / 礼器形制 / 明清宫廷 / 翡翠 / 和田玉 / 来源证书） |
| 按年代检索 | 红山 · 良渚 · 齐家 · 商周 · 战国 · 汉 · 唐宋 · 辽金元 · 明 · 清乾隆 … 共 16 项 |
| 收藏等级快搜 | 博物馆级 / 宫廷御制 / 高古玉 / 明清白玉 / 翡翠 A 货 / 入门通用 |
| 平台与拍卖行 | 12 家：Invaluable、LiveAuctioneers、the-saleroom、Christie's、Sotheby's、Bonhams、Woolley & Wallis、Roseberys、Lyon & Turnbull、嘉德/保利、Freeman's\|Hindman 等 |
| 寄拍名单 | 10 家玉器寄拍行，含负责部门、佣金说明、海外寄拍与适合度 |
| 竞拍避坑要点 | 翡翠 A/B/C 货证书、高古玉来源、出土文物合规、佣金税费、jade 一词的软玉/硬玉陷阱、先查历史成交 |

**平台搜索链接格式**

| 平台 | 模板 |
|------|------|
| Invaluable | `invaluable.com/search?keyword={q}&upcoming=true` |
| LiveAuctioneers | `liveauctioneers.com/search/?keyword={q}` |
| the-saleroom | `the-saleroom.com/en-gb/search-results?searchTerm={q}` |
| Christie's | `christies.com/en/search?keyword={q}` |
| Sotheby's | `sothebys.com/en/search?query={q}` |
| Bonhams | `bonhams.com/search/?q={q}` |
| Barnebys | `barnebys.com/search?q={q}` |

**维护方式**：打开 `jade.html`，编辑 `<script>` 顶部数据数组 —— `AS_OF` / `AUCTIONS`（档期，`end` 字段可留空即不显示倒计时）/ `CATS`（品类图谱）/ `KW_GROUPS` / `ERAS` / `TIERS` / `PCARDS` / `CONSIGN` / `NOTES`。改完刷新浏览器即可，无需构建。

**数据时点**：2026-08-25。档期以各行官网日历为准；玉器无统一评级体系，站内不列具体估价，一切以平台页面为准。
