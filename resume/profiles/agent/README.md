# Agent 方向 Profile（预留）

此目录为 **AI Agent / LLM 应用** 方向的简历预留位，暂未实现。

## 启用步骤

当你准备投递 Agent 方向实习时，参照其他 profile（如 `../recommendation/`）创建：

1. `summary.tex` — 针对 Agent 岗的自我评价（突出 LLM 应用、工具调用、RAG 等）
2. `skills.tex` — 重组 `shared/skills_base.tex`，加入 Prompt 工程 / LangChain 等（待实际掌握后）
3. `build.tex` — 复制 `../recommendation/build.tex`，按需调整 `\input` 的经历

## 说明

Agent 方向与搜广推差异较大，技能栏可能需要补充新关键词。
**注意遵循 CLAUDE.md 的约定：只用实际掌握的技能，不填虚构经历。**
等你在该方向有真实项目（如做过一个 RAG demo、Agent 应用）后再补充。

编译时 build 脚本会自动跳过没有 `build.tex` 的 profile 目录。
