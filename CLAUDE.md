# CLAUDE.md — Internship Preparation

This file provides context for AI coding agents (Claude, Copilot, etc.) working in this repository.

## Project Overview

实习准备项目。Owner: 张钧瑞 (Zjrua)，哈工大应用统计研究生(2025-2028)。
目标岗位: 推荐算法/搜索算法/广告算法实习。

**架构核心：技能树是主体，简历和项目是果实。**
- `skill-tree/` — 主体：可视化学习路径 + 进度 + 成就（JSON 数据源 + 生成器）
- `resume/` — 果实：模块化 LaTeX 简历（节点达成后更新素材 = 结实）
- `projects/` — 果实：搜广推开源项目（被技能树节点按路径引用）

## Repository Structure

- `skill-tree/` — **主体**。`data/*.json` 唯一数据源（方向节点 + 成就）+ `tools/render.py` 生成器 → 所有方向合并成 `dist/skill-tree.html`(单画布知识图谱 DAG) + `dist/PROGRESS.md`(进度表)。详见 `skill-tree/README.md`
- `resume/templates/` — 7套 LaTeX 简历模板（sb2nov, jakegut, billryan, hijiangtao, luooofan, deedy, awesome-cv）
- `resume/shared/` — **模块化素材层**（单一数据源，所有 profile 共用，见下文）
- `resume/profiles/` — **岗位 profile**（每个岗位一个目录，组装+裁剪素材）
- `resume/build/` — 编译脚本 `build_profile.cmd` + PDF 输出
- `projects/` — 搜广推方向开源项目（DeepCTR-Torch, DeepMatch, FuxiCTR, RecSystem-Pytorch, OpenOneRec, generative-recommenders, HLLM）——纯跟踪文件(非 submodule)，技能树节点用相对路径引用
- `docs/` — 学习笔记

## Key Conventions

### Skill Tree（主体）

技能树系统沿用简历的"单一数据源"理念：**JSON 是唯一数据源，生成器产出 HTML + Markdown**。

#### 前端架构（侧栏单页应用 SPA）
`skill-tree.html` 是侧栏导航的单页应用，4 个板块靠 URL hash 路由切换（`#tree`/`#profile`/`#templates`/`#fruit`）：
- 🌳 技能树：单画布 DAG + 进度仪表盘 + 成就花田
- 👤 个人信息：读 `data/profile.json` 渲染（姓名/教育/技能/经历/竞赛）
- 📄 简历模板：扫描 `resume/templates/` 目录（render.py: scan_templates + TEMPLATE_META）
- 🍎 果实展示：扫描 `resume/profiles/` + `resume/build/*.pdf`（render.py: scan_fruits），卡片「打开 PDF」
- 侧栏底部进度环 = 整体任务完成率

#### 数据流
```
skill-tree/data/*.json  (✏️ 只改这里：方向节点 + profile.json + 成就)
        │  python skill-tree/tools/render.py
        ▼  合并所有方向 → 单张知识图谱 + 扫描 resume/
skill-tree/dist/skill-tree.html  (侧栏 SPA, 浏览器打开)
skill-tree/dist/PROGRESS.md      (进度表, GitHub/Obsidian 可读)
```

#### 数据格式
- 节点(node)：`{id, name, category, status, depends_on, tasks[]}`，进度 = 已完成 tasks/总数，自动算
- `tasks[]` 每项 `{id, title, done, resource}`，`resource` 用相对路径（相对 `skill-tree/`）链论文或 `projects/` 源码
- **跨方向共享**：同名 node id（`python`/`pytorch`/`ml_basics`/`fm`/`deepfm`）在多方向 JSON 里用同 id，渲染时自动去重合并成一个节点
- `depends_on` 可填节点 id 或分支 id（如 `"sequence"` → 自动解析成该分支末端节点）
- 成就(achievements.json)：`{id, icon, name, desc, tier, condition}`，condition `type` 见 skill-tree/README.md
- **个人信息(profile.json)**：`{name, contact, education, skills, experience, awards, ...}`。⚠️ 与 `resume/shared/*.tex` 是同一信息的两份表达，改一处必须同步另一处

#### 布局算法（render.py: compute_dag_layout）
- 所有方向的节点合并去重 → 一张 DAG
- 深度 = 从根（无依赖）出发的最长路径长度，迭代松弛算
- **基础（depth 0）在画布顶部**，向下逐层生长
- 同 depth 内按 (方向 order, 分支顺序) 排序聚拢，减少连线交叉
- 连线坐标在 Python 算定（节点绝对定位 left/top），前端 JS 只负责画贝塞尔曲线（从上往下）+ 进度高亮

#### 关键约定
- **改技能/成就/个人信息只动 `data/*.json`**，然后跑 `python skill-tree/tools/render.py`，不碰 render.py 除非加新功能
- **`dist/` 是生成产物，已 gitignore**，不要手动改、不要提交
- **render.py 零依赖纯标准库**；新增方向只需往 `data/` 丢 JSON（目录驱动自动发现，无需改代码）
- **不填虚构技能**：初始只放真实方向，节点 status 默认 `locked`，由 owner 逐步推进
- **节点的 resource 用相对路径引用 `projects/` 和 `resume/`**，不移动这些目录
- **模板元数据**在 render.py 的 `TEMPLATE_META` dict（id = templates/ 目录名），加新模板在这里登记
- **布局常量**（NODE_W/ROW_GAP 等）在 render.py 顶部，调间距改这里

#### 常见任务
```bash
# 重新生成 SPA（改 data/ 或 resume/ 内容后必跑）
python skill-tree/tools/render.py
```
- 加节点：在 `data/<方向>.json` 某分支的 `nodes` 加一项 → render.py
- 加新方向：复制现有方向 JSON → 改内容 → render.py（自动发现，无需登记）
- 加成就：在 `data/achievements.json` 加一项 → render.py
- 改个人信息：改 `data/profile.json`（⚠️ 同步改 `resume/shared/*.tex`）→ render.py
- 新增简历 PDF：`build_profile.cmd` 编译后，scan_fruits 自动发现，render.py 即可在果实板块打开

### LaTeX Resume

#### 模块化简历架构（重要）
简历采用 **素材与呈现分离** 的模块化设计：

```
resume/
├── shared/                  ← 素材单一数据源（改这里，所有 profile 同步）
│   ├── personal.tex         ← 姓名/邮箱/手机（占位符集中于此！）
│   ├── education.tex        ← 教育背景
│   ├── skills_base.tex      ← 技能碎片（\skillLang 等可复用命令）
│   └── experience/          ← 经历素材库（每条经历一个文件，带标签注释）
│       ├── physical_data.tex
│       ├── stats_modeling.tex
│       └── awards.tex
└── profiles/                ← 岗位 profile（只做组装+裁剪）
    ├── recommendation/      ← 推荐算法（build.tex + skills.tex + summary.tex）
    ├── search/              ← 搜索算法
    ├── ads/                 ← 广告算法
    └── agent/               ← 预留（AI Agent 方向，未实现）
```

**核心原则**：
- **个人信息只在 `shared/personal.tex` 改一处**，所有 profile 自动同步（避免多份简历信息不一致）
- 经历素材放 `shared/experience/`，profile 用 `\input{experience/xxx}` 按需引用
- 新增岗位 = 在 `profiles/` 下建目录，不动素材

#### 编译方式
- 编译用 **XeLaTeX**（中文模板必须）
- **统一用 `build/build_profile.cmd`** 一键编译（处理了 cls 字体路径 + TEXINPUTS 注入）：
  ```
  cd resume/build
  build_profile.cmd                    # 编译所有 profile
  build_profile.cmd recommendation     # 只编译推荐 profile
  ```
- PDF 输出到 `resume/build/<profile>.pdf`
- 编译机制：从 `templates/billryan/` 目录运行 xelatex（因 cls 用相对路径引用字体），通过 `TEXINPUTS` 把 `shared/` 和 profile 目录注入 LaTeX 搜索路径

#### 字体说明
- `billryan`、`hijiangtao`、`luooofan`、`deedy` 的 `fonts/` 目录均**未纳入版本控制**（体积大）
- `billryan/fonts/` 已在本地补全（Main 西文 + zh_CN-Adobe 中文 + fontawesome），克隆后需重新获取
- 获取方式：`git clone -b zh_CN git@github.com:billryan/resume.git` 后复制其 `fonts/` 目录

#### 占位符（待替换）
- 邮箱 `your.email@example.com`、手机 `(+86) xxx-xxxx-xxxx` 在 `shared/personal.tex`
- 收到真实信息后只改这一个文件，重新编译即可

#### 旧的单文件简历
- 各模板目录下的 `zhang_junrui.tex` 是**早期的单文件版本**（内容已迁移到模块化架构）
- 模块化 profile 是当前主推方式，旧文件保留作参考

### Personal Info (for resume)
- **姓名**: 张钧瑞
- **学校**: 哈尔滨工业大学 (HIT)
- **学历**: 本科 信息与计算科学 (2020-2024) → 研究生 应用统计 (2025-2028)
- **技能**: Python, PyTorch, LaTeX, C++(基础)
- **邮箱/手机**: 占位符，待替换
- **竞赛**: 2022美赛M奖, 2023国赛黑龙江省二等奖
- **项目**: physical_data论文投《体育科学》, 2026统计建模大赛研究生组(TJJM20260414180979)
- **GitHub**: Zjrua

## What Not to Do

- 不要删除 `projects/` 下的源代码文件（这些是学习参考）
- 不要修改各开源项目的代码逻辑（如需实验改动，另建分支或副本）
- 不要在 resume 模板中填入虚构的经历或数据
- 不要将编译产物（.aux, .log, .fls 等）提交到 git
- 不要手动改 `skill-tree/dist/`（生成产物，已 gitignore）；改技能树只动 `skill-tree/data/*.json` 再跑 render.py
- 不要移动 `resume/` 或 `projects/`（技能树用相对路径引用它们）

## Common Tasks

### 编译简历
```cmd
cd resume\build
build_profile.cmd                    REM 编译所有 profile，输出到 build\<profile>.pdf
build_profile.cmd recommendation     REM 只编译推荐 profile
```

### 更新个人信息
**只改 `resume/shared/personal.tex` 一个文件**（邮箱/手机/姓名），所有 profile 自动同步。

### 新增一个岗位 profile
1. 在 `resume/profiles/<new-role>/` 下建目录
2. 复制 `recommendation/` 的 `build.tex` / `skills.tex` / `summary.tex`
3. 修改 `summary.tex`（针对该岗位的自我评价）和 `skills.tex`（重组技能排序）
4. 运行 `build_profile.cmd <new-role>` 验证

### 查看项目代码
直接在 `projects/` 下阅读源码，无需安装（除非要运行实验）。

## Tech Stack

- **LaTeX**: XeLaTeX + ctex (中文模板)
- **Python**: 3.x + PyTorch (projects/ 下的模型代码)
- **Git**: SSH protocol (git@github.com:Zjrua/)
