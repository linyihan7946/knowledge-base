# Wiki Schema

## Domain
个人知识库 — 涵盖 AI/编程/工作/生活/健康/教育/旅游等全方位个人笔记。

## Conventions
- 文件名：小写，连字符，无空格（如 `python-basics.md`）
- 每个 wiki 页面以 YAML frontmatter 开头（见下方）
- 使用 `[[wikilinks]]` 在页面间链接（每个页面至少 2 个出站链接）
- 更新页面时，始终更新 `updated` 日期
- 每个新页面必须在 `index.md` 的对应分类下添加条目
- 每个操作必须追加到 `log.md`
- **来源标记：** 综合 3+ 来源的页面，在段落末尾追加 `^[raw/mubu/来源文件.md]`，便于追溯
- **原始文件只读：** `raw/mubu/` 目录下的文件是只读的，绝不修改

## Frontmatter
  ```yaml
  ---
  title: 页面标题
  created: YYYY-MM-DD
  updated: YYYY-MM-DD
  type: entity | concept | comparison | query | summary
  tags: [来自下方标签体系]
  sources: [raw/mubu/来源文件.md]
  # 可选质量信号：
  confidence: high | medium | low        # 声明的支持程度
  contested: true                        # 存在未解决的矛盾时设置
  contradictions: [其他页面slug]         # 与此页面冲突的页面
  ---
  ```

`confidence` 和 `contested` 是可选的，但对于观点性强或快速变化的主题推荐设置。
除非声明得到多个来源的支持，否则不要标记 `high`。

### raw/ Frontmatter

原始来源也添加一个小的 frontmatter 块，以便重新摄入时检测变化：

```yaml
---
source_url: https://example.com/article   # 原始 URL（如果适用）
ingested: YYYY-MM-DD
sha256: <下方原始内容的 hex 摘要>
---
```

`sha256:` 允许未来重新摄入相同 URL 时，内容未变则跳过，变化则标记并更新。

## Tag Taxonomy

### AI/技术
- ai, model, architecture, training, inference, fine-tuning
- deep-learning, machine-learning, neural-network
- computer-vision, nlp, speech
- rag, knowledge-graph, agent
- image-generation, video-generation, text-to-image
- llm, transformer, diffusion

### 编程/开发
- programming, python, javascript, typescript, rust, c++, c#
- frontend, backend, fullstack
- web, threejs, webgl, webgpu
- database, sql, mysql
- git, docker, linux
- ide, tool, framework, library

### 工作/项目
- work, project, design-system, cad, bim
- pointcloud, 3d, rendering
- optimization, performance, architecture
- team, meeting, weekly-report

### 生活/健康
- health, fitness, diet, sleep, mental-health
- life, food, travel, shopping
- car, house, electronics
- family, education, parenting

### 媒体/创作
- video, editing, animation, design
- social-media, douyin, bilibili
- ai-tool, productivity

### 元数据
- comparison, timeline, reference, howto, note

规则：页面上的每个标签必须出现在此标签体系中。如果需要新标签，先在这里添加，然后使用。

## Page Thresholds
- **创建页面：** 当实体/概念在 2+ 来源中出现，或在一个来源中是核心主题
- **添加到现有页面：** 来源提到已覆盖的内容
- **不创建页面：** 临时提及、次要细节或领域外的内容
- **拆分页面：** 超过 ~200 行时，拆分为子主题并添加交叉链接
- **归档页面：** 内容完全被取代时，移至 `_archive/`，从索引中移除

## Entity Pages
每个值得注意的实体一个页面。包括：
- 概述/是什么
- 关键事实和日期
- 与其他实体的关系（[[wikilinks]]）
- 来源引用

## Concept Pages
每个概念或主题一个页面。包括：
- 定义/解释
- 当前知识状态
- 开放问题或讨论
- 相关概念（[[wikilinks]]）

## Comparison Pages
并排分析。包括：
- 比较什么和为什么
- 比较维度（表格格式优先）
- 结论或综合
- 来源

## Update Policy
当新信息与现有内容冲突时：
1. 检查日期 — 较新的来源通常取代较旧的
2. 如果确实矛盾，记录两个立场并标注日期和来源
3. 在 frontmatter 中标记矛盾：`contradictions: [页面名称]`
4. 在 lint 报告中标记供用户审查
