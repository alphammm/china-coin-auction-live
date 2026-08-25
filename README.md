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

---

## 🔴 实时抓取：海外中国古玉在拍数据

**范围**：中国大陆以外的拍卖行 / 聚合平台 · 中国古玉与翡翠 · **清代及以前**（自动排除 20 世纪、民国及以后）。

### 为什么抓取跑在 GitHub Actions 上

纯前端不可能跨域抓各拍行库存（CORS + 反爬），所以：

```
GitHub Actions（每 3 小时）→ scraper/core.py 抓取 27 个海外源
        → 归一化 / 分类 / 去重 → data/lots.json + data/lots.js
        → 回写仓库 → jade.html 读取并渲染「实时在拍」区
```

`data/lots.js` 是 `window.__JADE_DATA__ = {...}` 包裹版，双击用 `file://` 打开页面时也能读到；
用 http 打开时页面会额外 `fetch` 一次 `lots.json` 取最新。

### 抓取器结构

| 文件 | 作用 |
|------|------|
| `scraper/sources.yml` | **唯一需要改的地方**。新增一家拍行 = 加一段配置，不动代码 |
| `scraper/core.py` | 抓取、解析、归一化、分类、过滤、去重、产出 |
| `.github/workflows/scrape-jade.yml` | 定时 / 手动 / push 触发 |

**三级降级解析**（先成功者胜，实际命中的策略会写进健康报告）：

1. `configured` — `sources.yml` 里写好的 CSS 选择器
2. `jsonld` — 页面内嵌 schema.org JSON-LD（`Product` / `ItemList`）
3. `links` — 按 `lot_url_pattern` 正则捞链接 + 锚文本（最保底，多数站点都能出货）

另支持 `method: json` 直连 JSON API（`json:` 段写点号取值路径）。

### 收录口径（`core.py` 中的正则）

- **必须命中玉**：`jade / jadeite / nephrite / 玉 / 翡翠`（`hardstone` 需另有中国信号）
- **必须有中国语境**：标题含 `chinese/qing/ming/qianlong/hongshan/…` 或检索词本身即中国向
- **年代 ≤ 清**：`高古（新石器–汉）/ 唐宋辽金 / 元明 / 清 / 未标注` 放行；
  命中 `20th century / republic period / art deco / 现代` 一律剔除
- **材质分类**：翡翠（硬玉）/ 和田玉·软玉（软玉）/ 未标注

### 运行方式

```bash
# 本地跑（需要能出网的环境）
pip install -r scraper/requirements.txt
python scraper/core.py                     # 正式抓取，产出 data/
python scraper/core.py --probe             # 探测模式：打印各源响应特征 + 三种解析器命中数
python scraper/core.py --only=auctionet,bonhams   # 只跑指定源
```

在 GitHub 上：Actions → 「抓取海外中国古玉拍品」→ Run workflow（可选 `probe` 模式）。
推送 `scraper/` 下的改动也会自动触发一次。

> ⚠️ **cron 只在默认分支生效** —— 每 3 小时自动刷新要等本分支合入 `main` 之后才会开始。
> 在此之前用手动触发 / push 触发。

### 页面上的「抓取源状态」

页面「实时在拍」区底部有一个折叠面板，逐源列出**抓到多少 / 命中多少 / 用了哪级解析 / HTTP 状态**。
被 Cloudflare 或 bot 墙拦住的源会显示 403，方便直接判断是选择器要改还是该源根本抓不动。

### 当前战况（2026-08-25 实测）

| 指标 | 数值 |
|------|------|
| 在拍条目 | **897 条**（每轮累积合并，非全量覆盖） |
| 带图 | **895 / 897** |
| 年代分布 | 高古 **250** · 清 **202** · 元明 11 · 唐宋辽金 7 · 未标注 427 |
| 有产出的源 | 6 / 76：Auctionet、HiBid、Invaluable、the-saleroom、i-bidder、Sotheby's |
| 单轮原始命中 | 约 4,500 条 → 经年代/赝品口径过滤 + 去重 |

**为什么只有 6 个源有产出，却覆盖了大量中小拍行**：这 6 个里 4 个是聚合平台
（HiBid 聚合北美数千家、the-saleroom 与 i-bidder 同属 ATG 聚合英国上千家、
Invaluable 全球聚合），一个源就带出几十家中小行的拍品。富化顺利的轮次里
拍行名会还原成 Adam's、Galerie Zacke、Hannam's、Aalders、Fung Ngai(HK) 等
60+ 家真实拍行。

**其余 70 个源为什么没产出**（页面「抓取源状态」逐个如实标注，不假装有数据）：

| 状态 | 家数 | 说明 |
|------|------|------|
| 检索地址无效 404 | ~30 | 推测的搜索 URL 与实际路径不符，需按探测的链接形态逐个校正 |
| 反爬拦截 403 | ~8 | Bonhams、Heritage、Catawiki、Michaan's 等在 CDN 层拒绝数据中心 IP |
| 人机挑战页 202 | ~8 | ATG 系与部分英国行返回 Cloudflare 挑战 |
| 页面可取但未解析出拍品 | ~24 | 搜索页能打开，结果区结构尚未适配 |

这是可逐轮收敛的工程：带 `[probe]` 的提交或手动 dispatch 会打印各家的
「站内链接形态直方图」，据此校正 `sources.yml` 的搜索地址与 lot 链接规律。

**已知短板**：详情页回访常被限流，估价与拍行名的富化成功率在轮次间波动很大
（实测 204 → 19）；已改为增量合并（新一轮继承上一轮富化好的字段、
近期见过的条目保留 5 天）来削平抖动，但根治要靠给主力聚合站写卡片级选择器。

### 字段是怎么拿到的

搜索页只负责**发现 lot 链接**（三级降级解析，多数走链接正则兜底），
字段一律回**拍品详情页**取 —— 几乎每家详情页都有 `og:` 标签或 schema.org
`Product`，标题、图片、估价、拍行名在那里干净且统一。8 并发回访，
富化后重新分类年代/材质并二次过滤（`20th century`、`faux`、`in the style of`
这类词到这一步才暴露）。截拍时间若详情页没给，则由搜索卡片上的
「3 days / 21 hours」折算为近似值，前端标注为「约」。
