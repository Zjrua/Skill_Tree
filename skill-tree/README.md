# 🌳 技能树系统（Skill Tree）

> 本仓库的**主体**。用可视化的技能树规划实习学习路径，清单驱动进度，成就给反馈。
> 简历（`resume/`）和开源项目（`projects/`）是这棵树结出的**果实**，被节点按路径引用。

## 一句话理念

和简历模块化架构同源：**JSON 是唯一数据源，生成器产出 HTML + Markdown**。
改一处 JSON，技能树、进度表、成就墙全部同步——不存在多处维护、进度脱节的问题。

## 泛化设计

系统**不绑定任何具体领域**。`data/` 目录下每个 `*.json`（除 `achievements.json`、`profile.json`）自动识别为一个方向。
未来想加新实习方向（如 AI Agent、数据分析），只需往 `data/` 丢一个 JSON，无需改任何代码。
展示顺序由 JSON 里的 `"order"` 字段控制。

## 单页应用（侧栏四大板块）

`skill-tree.html` 是一个**侧栏导航的单页应用**，左侧固定侧栏切换四个板块，URL hash 同步（`#tree`/`#profile`/`#templates`/`#fruit`），刷新保持当前板块：

| 板块 | 内容 |
|------|------|
| 🌳 技能树 | 单画布知识图谱（DAG）+ 进度仪表盘 + 成就花田 |
| 👤 个人信息 | 姓名/联系方式/教育/技能/项目经历/竞赛（数据源 `profile.json`）|
| 📄 简历模板 | 扫描 `resume/templates/` 的 7 套模板，卡片展示风格/语言/场景 |
| 🍎 果实展示 | 扫描 `resume/profiles/` + `resume/build/*.pdf`，卡片「打开 PDF」 |

侧栏底部有整体进度环 + 成就/任务统计。

## 单画布知识图谱（DAG）

所有方向的节点**合并到一张大图**上，不再按方向/分支割裂。

- **去重**：跨方向同名节点（`python`/`pytorch`/`ml_basics`/`fm`/`deepfm` 在多个方向都出现）按 node id 去重，只画一次——它们就是各方向**共享的基础**
- **深度**：每个节点按 `depends_on` 算出"从根出发的最长路径长度"，根节点（无依赖）= depth 0
- **基础在上**：depth 0 的根节点（python / stats）画在画布**最顶部**，向下逐层生长
- **连线**：每条依赖用**贝塞尔曲线**连接（从上往下），前端 JS 按算定的坐标绘制。**已完成的依赖段高亮成生长绿**，未解锁的暗淡
- **方向着色**：节点下方的小色点标注它属于哪个方向（推荐🟢/搜索🟢/广告🟡），共享节点显多色

> 之所以不是严格的树而是 DAG：一个节点可以依赖多个父节点（如 `deepfm ← fm + dnn`），
> 只要能在一张图上体现知识的前后联系即可。

## 目录

```
skill-tree/
├── data/                       ← ✏️ 数据源（你只改这里）
│   ├── recommendation.json       推荐方向节点（召回/精排/序列/大模型）
│   ├── search.json               搜索方向节点（召回/LTR/向量检索）
│   ├── ads.json                  广告方向节点（CTR/多任务/机制）
│   ├── profile.json              个人信息（姓名/教育/经历，⚠️ 须与 resume/shared/*.tex 同步）
│   └── achievements.json         成就定义（全局通用）
├── tools/
│   └── render.py                 生成器（零依赖纯 Python）
└── dist/                        ← 🔧 生成产物（已 gitignore）
    ├── skill-tree.html           侧栏单页应用（浏览器打开）
    └── PROGRESS.md               Markdown 进度表（GitHub/Obsidian 可读）
```

## 快速开始

```bash
# 1. 重新生成树（改了 data/*.json 后必跑）
python skill-tree/tools/render.py

# 2. 浏览器打开
start skill-tree/dist/skill-tree.html      # Windows
open skill-tree/dist/skill-tree.html       # macOS
```

浏览器里：
- **点节点卡片** → 展开子任务清单和资源链接
- **勾选子任务** → 进度即时刷新，状态自动存浏览器 `localStorage`（刷新不丢）

## 日常学习怎么用

1. 学完一个子任务 → 在浏览器里勾掉它
2. 一个节点的子任务全勾完 → 节点变 ✅，相关分支进度上涨
3. 想让进度进 git（换设备/分享）→ 把 JSON 里对应 task 的 `done` 改成 `true`，重跑 `render.py`
4. 节点达成 → 记得回头更新简历素材（`resume/shared/`），这叫**结出果实**

## 数据格式

**节点**（`data/<方向>.json` → branches → nodes）：

```jsonc
{
  "id": "deepfm",                    // 全局唯一（跨方向共享时同 id → 自动去重合并）
  "name": "DeepFM",
  "category": "精排/CTR",
  "status": "learning",              // locked | learning | done（与 tasks 综合判断）
  "depends_on": ["fm", "dnn"],       // 前置节点 id；决定在图里的位置与连线
  "tasks": [                         // 清单 = 进度内核
    {"id": "paper", "title": "读 DeepFM 论文", "done": true,
     "resource": "https://arxiv.org/abs/1703.04247"},
    {"id": "source", "title": "读 deepfm.py", "done": true,
     "resource": "../../projects/DeepCTR-Torch/deepctr_torch/models/deepfm.py"}
  ]
}
```

- 节点进度 = `已完成 tasks / 总 tasks`，自动算
- `resource` 用相对路径（相对 `skill-tree/`）链接到论文或 `projects/` 源码
- **跨方向共享**：`python`/`pytorch`/`ml_basics`/`fm`/`deepfm` 在多个方向的 JSON 里用**同 id**，
  渲染时自动去重合并成一个节点（即共享根系），节点会标注它归属的多个方向
- `depends_on` 也可以填**分支 id**（如 `"sequence"`），生成器会自动解析成该分支的末端节点

**成就**（`data/achievements.json`）：

```jsonc
{
  "id": "recall_master", "icon": "🪝", "name": "召回大师",
  "desc": "完成推荐方向「召回」整支分支", "tier": "silver",
  "condition": {
    "type": "branch_done",            // 见下表
    "tree_id": "recommendation", "branch_id": "recall"
  }
}
```

支持的 condition `type`：

| type | 触发条件 | 示例参数 |
|------|----------|----------|
| `nodes_done` | 已完成节点数 ≥ min | `{"min": 1}` |
| `tasks_done` | 已完成子任务数 ≥ min | `{"min": 10}` |
| `tree_progress` | 任一树进度 ≥ min(%) | `{"min": 50}` |
| `all_trees_progress` | 所有树进度各 ≥ min(%) | `{"min": 30}` |
| `branch_done` | 某分支所有节点 done | `{"tree_id":"...","branch_id":"..."}`（tree_id 可省，匹配任意树） |
| `task_resource_contains` | 已完成任务里 resource 含 substring 的 ≥ min | `{"substring":"arxiv","min":5}` |
| `task_keyword` | 已完成任务里 title 含 keyword 的 ≥ min | `{"keyword":"论文","min":5}` |

`tier` 取值：`bronze` 🥉 / `silver` 🥈 / `gold` 🥇。

## 常见操作

**加一个新技能节点**：在对应 `data/<方向>.json` 的某个 branch 的 `nodes` 里加一项 → `render.py`

**加一个新分支（实习方向）**：在树 JSON 的 `branches` 里加一个 branch 对象 → `render.py`

**加一个新方向**（如未来 AI Agent，与搜广推不相关）——**不用改任何代码**：
1. 复制 `recommendation.json` → `agent.json`，改内容（设 `tree_id`、`title`、`order` 决定展示顺序、`color` 取主题色）
2. `python skill-tree/tools/render.py` —— 目录驱动加载会自动发现新方向，节点合并进同一张图

**加成就**：在 `achievements.json` 加一项 → `render.py`
