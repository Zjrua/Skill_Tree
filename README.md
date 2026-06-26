# 🌳 实习技能树

实习准备项目。**技能树是主体**——用它规划学习路径、追踪进度、解锁成就；
简历和开源项目是这棵树结出的**果实**。

> Obsidian / Notion / 飞书是对**已有知识**的总结；技能树是对**未来学习路径**的规划，有明确的进度反馈。

```
   所有实习方向的技能 → 合并成一张知识图谱(DAG)
            │  基础(Python/统计)在上，向下生长成枝叶
            │
   ┌────────┼─────────┐
   ▼        ▼         ▼
🎯推荐   🔍搜索    📢广告      ← 节点的方向归属(着色)
   │        │         │
   ▼        ▼         ▼
📄 简历成品(PDF)     📦 开源项目   ← 果实(resume/ + projects/)
```

不再按方向割裂成几棵树——**整个仓库就是一棵树**。基础（Python/PyTorch/统计等）在上，
向下生长成各方向的枝叶。前端是**侧栏导航的单页应用**：技能树 / 个人信息 / 简历模板 / 果实展示 四个板块切换。

## 目录结构

```
├── skill-tree/              ← 【主体】技能树系统（侧栏单页应用）
│   ├── data/                  ✏️ 数据源(只改这里)：方向节点 + 个人信息 + 成就
│   │   ├── recommendation.json  推荐：召回/精排/序列/大模型推荐
│   │   ├── search.json          搜索：召回倒排/LTR/向量检索
│   │   ├── ads.json             广告：CTR/多任务/创意机制
│   │   ├── profile.json         个人信息(姓名/教育/经历，⚠️ 须与 resume/shared 同步)
│   │   └── achievements.json    全局成就(铜/银/金)
│   ├── tools/render.py         🔧 生成器：JSON → 侧栏单页应用 + Markdown
│   └── dist/                   🔧 产物(已 gitignore)
│       ├── skill-tree.html       侧栏单页应用(4 板块, 浏览器打开)
│       └── PROGRESS.md           进度表(GitHub/Obsidian 可读)
├── resume/                  ← 【果实】简历
│   ├── shared/                 素材单一数据源(个人信息/教育/经历)
│   ├── profiles/               岗位 profile(推荐/搜索/广告)
│   ├── templates/              7套 LaTeX 模板
│   └── build/                  编译脚本 + PDF 输出
├── projects/                ← 【果实】搜广推开源项目(学习/复现参考)
└── docs/                    ← 学习笔记
```

详见 [skill-tree/README.md](skill-tree/README.md)。

## 核心理念

沿用简历模块化架构的思路——**单一数据源，呈现与内容分离**：

| | 简历系统 | 技能树系统 |
|---|---|---|
| 数据源 | `resume/shared/` | `skill-tree/data/*.json` |
| 产物 | `resume/build/*.pdf` | `skill-tree/dist/skill-tree.html` |
| 生成 | XeLaTeX + build_profile.cmd | `python render.py` |
| 原则 | 改一处素材，多份简历同步 | 改一处 JSON，树/进度/成就同步 |

技能树节点用相对路径**引用**简历和项目（`resource` 链论文/源码，`fruit` 链对应简历 profile），不改它们的位置。

## 快速开始

```bash
# 1. 生成技能树（改 data/*.json 后必跑）
python skill-tree/tools/render.py
# 2. 浏览器打开
start skill-tree/dist/skill-tree.html
```

浏览器里：**左侧侧栏切换四个板块**——🌳技能树（一张图看所有节点和依赖连线，基础在上）、👤个人信息、📄简历模板、🍎果实展示（打开编译好的 PDF）。点节点看子任务、勾选记录进度（自动存 localStorage），或读 `skill-tree/dist/PROGRESS.md` 看总览。

## 日常学习循环

1. **学** → 在「技能树」板块勾掉子任务（或改 JSON 的 `done` 重跑 render.py）
2. **节点达成** → 回头把学到的东西写进 `resume/shared/`（结出果实）
3. **看反馈** → 进度上涨、依赖连线变绿、成就解锁；侧栏进度环实时更新
4. **投简历** → `cd resume/build && build_profile.cmd <profile>` 出 PDF → 到「果实展示」板块打开

## 图谱内容（基于真实 projects/）

| 方向 | 路径 | 对应开源项目 |
|------|------|--------------|
| 🎯 推荐 | 基础→召回→精排/CTR→序列→大模型推荐 | DeepMatch / DeepCTR-Torch / FuxiCTR / RecSystem-Pytorch / generative-recommenders / HLLM / OpenOneRec |
| 🔍 搜索 | 基础→召回倒排→排序(LTR) | DeepMatch (DSSM) |
| 📢 广告 | 基础→CTR预估→多任务/转化→创意机制 | DeepCTR-Torch (含 multitask) / FuxiCTR |

三方向共享的基础（Python/PyTorch/统计等）用同名 node id 在图里自动去重，汇聚成根系。

## 编译简历

```cmd
cd resume\build
build_profile.cmd                    :: 编译所有 profile → build\<profile>.pdf
build_profile.cmd recommendation     :: 只编译推荐算法岗
```

首次使用补字体（billryan 等 `fonts/` 因体积未入 git）：见 [CLAUDE.md](CLAUDE.md)。

## 设计原则

- **只改 JSON**：加技能/成就/分支只动 `data/`，不碰代码
- **不填虚构技能**：初始只放 CLAUDE.md 确认的真实方向，节点默认 `locked`，由你逐步推进
- **零依赖**：生成器纯 Python 标准库，Windows 直接能跑

## 许可

各模板和开源项目遵循其原始许可证；技能树系统（`skill-tree/`）为本人原创。
