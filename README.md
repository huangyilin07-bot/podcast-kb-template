# 播客知识库

把听过的小宇宙播客自动变成 Notion 里可检索、可复习的知识库。支持 Claude Code 和 Codex 两种 AI 编程工具。

发一条小宇宙单集链接给 AI，它会完成：

1. 下载音频并在本地转写（不需要任何语音识别 API key）
2. 按固定模板整理：一页纸摘要、带时间戳的大纲、核心观点、方法论框架、检查清单、关键原话
3. 分类写入你自己的 Notion 数据库，并关联库里其他单集
4. 按间隔重复（3 / 10 / 30 / 90 天）安排复习，防止「听过就忘」

## 选一种用法

| | 路线 A：Claude Code 网页版 | 路线 B：Codex 命令行（本机） |
| --- | --- | --- |
| 运行位置 | 云端，打开浏览器就能用 | 你自己的电脑（Mac 或 Linux；Windows 需用 WSL） |
| 需要安装 | 无 | Python 3、ffmpeg、Codex CLI |
| 网络设置 | 需要在云环境里放行小宇宙域名 | 无需设置，Codex 联网时批准即可 |
| 连接 Notion | claude.ai 里一键连接 | 终端运行一条登录命令 |
| 账号 | claude.ai 账号 + GitHub 账号 | ChatGPT / OpenAI 账号 |

两条路线用的是同一套规则（`AGENTS.md`），整理出来的格式一致；提炼观点的深浅取决于所用模型。

---

## 路线 A：Claude Code 网页版

### A1. 复制这个仓库

在本仓库页面点右上角绿色按钮 Use this template → Create a new repository。Owner 选你自己，可见性选 Private，然后创建。

### A2. 连接 GitHub 和 Notion

打开 claude.ai → Settings → Connectors：

- 连接 GitHub，并在授权页面允许 Claude 访问刚创建的仓库（选 All repositories 最省事）
- 连接 Notion，授权你想放知识库的工作区

### A3. 开一个会话并设置网络

1. 打开 claude.ai/code，新建会话，选择你刚创建的仓库。
2. 点会话标题栏里的云环境菜单 → Edit → Network access，在 Allowed domains 里加入：

   ```
   www.xiaoyuzhoufm.com
   media.xyzcdn.net
   ```

   保留「Allow package managers」的勾选。若提示语音模型下载失败，再加入 `github.com` 和 `objects.githubusercontent.com`。

3. 第一次启动会自动下载语音模型（约 170MB），多等 1 分钟左右。

### A4. 首次设置

在会话里发「开始设置」，然后跳到下方「首次设置会发生什么」。

---

## 路线 B：Codex 命令行（本机）

### B1. 安装基础工具（只需一次）

Mac（需先装 [Homebrew](https://brew.sh)）：

```bash
brew install python ffmpeg git
npm install -g @openai/codex   # 或按 Codex 官方文档安装
```

Ubuntu / WSL：

```bash
sudo apt install python3 python3-venv ffmpeg git curl
npm install -g @openai/codex
```

### B2. 下载这个项目并安装

推荐先在 GitHub 上用 Use this template 复制一份到你自己的账号（方便保存配置），然后：

```bash
git clone https://github.com/<你的用户名>/<你的仓库名>.git podcast-kb
cd podcast-kb
./setup.sh
```

`setup.sh` 会创建独立的 Python 环境、安装依赖并下载语音模型（约 170MB），大约 2–3 分钟。

### B3. 连接 Notion

项目里的 `.codex/config.toml` 已经配好了 Notion 官方的 MCP 服务，你只需要登录一次：

```bash
codex mcp login notion
```

浏览器会打开 Notion 授权页，选择你想放知识库的工作区。如果命令不可用或项目配置未生效，按 [Notion 官方的 Codex 接入说明](https://developers.notion.com/docs/get-started-with-mcp) 把同样的配置写进 `~/.codex/config.toml`。

### B4. 首次设置

在项目目录里启动 Codex：

```bash
codex
```

发「开始设置」。Codex 第一次下载小宇宙音频时会请求联网权限，选择允许。

---

## 首次设置会发生什么

AI 会问你知识库放在 Notion 哪个页面下，确认领域分类，然后自动建好数据库、视图和规范页，并把配置保存到 `kb.config.json`。之后每次使用都会直接用这个库。

## 日常使用

（路线 A：新开会话时选择你的仓库；路线 B：在项目目录里运行 `codex`）

| 你发的内容 | AI 做什么 |
| --- | --- |
| 小宇宙单集链接 | 转写、整理、入库，回复页面链接和一句话核心 |
| 「查：我听过哪些关于定价的方法论」 | 检索知识库，综合回答并标注出自哪一期、哪个时间点 |
| 「聚合：增长」 | 把多期节目里同主题的方法论合并成一页，标出共识与分歧 |
| 「复习」 | 取到期的单集，每期出 3 道回忆题，答完自动排下次复习 |
| 「应用：我下周要做一场产品发布」 | 从库里调取相关方法论，转成这件事的检查清单 |

一期 1–2 小时的节目，转写约 5 分钟（本机速度取决于电脑性能），整理和写入 Notion 约 10 分钟。

也可以只转写不入库：`./ingest.sh <小宇宙链接>`，逐字稿保存在 `episodes/` 下。

## 可选设置

修改 `kb.config.json`（首次设置后生成）：

- `save_transcript`：是否把逐字稿也写进 Notion。设为 `false` 可以明显加快入库，逐字稿只保留在本地 `episodes/`。
- `extra_rules`：你自己的额外规则，例如「涉及医疗建议的内容加风险提示」。

也可以直接告诉 AI 你想怎么改，比如「领域加一个『投资理财』」。修改规则请改 `AGENTS.md`（`CLAUDE.md` 只是引用它）。

## 注意事项

- 目前只支持小宇宙单集链接。
- 只分享工具，不分享内容。整理出来的逐字稿和总结基于节目方的作品，仅供个人学习，请勿公开发布或转售。
- 转写模型：使用 [sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx) 发布的 SenseVoice 模型（转换自 ASLP-lab/WSYue-ASR）。个人使用前可自行查看其许可条款。
- 转写不区分说话人，人名和专有名词会有同音错字。AI 会按上下文纠正，并在每页末尾列出校对说明，引用前建议回听核实。
- 路线 A 的云端会话是临时环境，音频和本地逐字稿会在会话结束后清除；整理好的内容都在你的 Notion 里，不受影响。
- 使用过程消耗的是你自己 AI 账号的用量。
