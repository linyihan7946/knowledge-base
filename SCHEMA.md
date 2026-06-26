# Wiki Schema

本项目把 `raw/notes` 和 `raw/ai` 中的原始 Markdown 笔记整理成 `wiki/` 下的结构化页面，并继续用于浏览、检索和 RAG 问答。

## 页面类型

- `concept`：概念、方法、流程、主题
- `entity`：人物、产品、项目、工具、组织、地点
- `comparison`：并列比较、方案取舍

## Wiki 页面 Frontmatter

```yaml
---
title: 页面标题
created: YYYY-MM-DD
updated: YYYY-MM-DD
type: concept
tags: [ai, productivity]
sources: ["raw/notes/example.md"]
confidence: medium
---
```

## 原始笔记 Frontmatter

原始笔记可以没有 frontmatter。推荐格式：

```yaml
---
title: 原始笔记标题
source_url: https://example.com
ingested: YYYY-MM-DD
---
```

## 写作规范

- 每个页面聚焦一个主题。
- 优先使用 `[[wikilinks]]` 连接相关页面。
- 页面内容应能独立阅读，不只是一组关键词。
- 有来源时保留 `sources`，方便追溯。
- 短暂想法、临时碎片可以先进入 `raw/ai`，后续再整理。

## 标签建议

常用标签：

```text
ai, llm, rag, knowledge-graph, agent, productivity,
programming, python, javascript, frontend, backend,
tool, workflow, project, work, design, video,
health, life, travel, education, note, reference
```

标签不需要过度精细，稳定、可复用比数量多更重要。
