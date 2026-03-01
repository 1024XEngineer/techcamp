# 系统提示词架构

## 当前实现的核心思路

`mini-claude-code` 的系统提示词不是纯静态字符串，而是运行时组装：

1. 静态核心指令（`src/SYSTEM_PROMPT.md`）
2. 可选运行时状态（`runtimeHints`，例如上下文压缩摘要）

对应实现在 `src/agent/prompt.ts`：

```typescript
const PROMPT_FILE = join(import.meta.dir, '../SYSTEM_PROMPT.md')

export async function assembleSystemPrompt(runtimeHints: string[] = []): Promise<string> {
  const segments: string[] = []

  // Segment 1: 静态指令
  segments.push(await Bun.file(PROMPT_FILE).text())

  // Segment 2: 运行时状态（有则注入）
  if (runtimeHints.length > 0) {
    segments.push('---\n# 运行时状态\n\n' + runtimeHints.join('\n\n'))
  }

  return segments.join('\n\n')
}
```

## 分段结构

```text
┌─────────────────────────────────────────────────────┐
│ Segment 1: 静态核心指令                             │
│ 来源：src/SYSTEM_PROMPT.md                          │
│ 内容：角色、行为准则、工具使用建议、输出规范         │
├─────────────────────────────────────────────────────┤
│ Segment 2: 运行时状态（可选）                        │
│ 来源：runtimeHints                                  │
│ 内容：压缩摘要、阶段性约束、会话重建提示             │
└─────────────────────────────────────────────────────┘
```

## 与工具描述的关系

工具参数 schema 与描述由 `tools: TOOLS` 传给 `generateText`，不在 `assembleSystemPrompt` 里重复拼接。

也就是说：
- 提示词层主要放行为策略
- 工具参数规范由 `tool({ description, parameters })` 提供

这样可以避免“提示词里写一份、代码里写一份”导致的双份漂移。

## 运行时状态注入示例

上下文压缩后，`index.ts` 会把摘要写入 `runtimeHints`，下轮请求自动注入系统提示词：

```typescript
const summary = await compressHistory(history)
const hint = buildCompressionHint(summary)
history = []
runtimeHints = [hint]
```

生成的 Segment 2 形态如下：

```markdown
---
# 运行时状态

[执行历史摘要 - 之前会话已压缩]
...
请基于摘要继续完成原始任务，不要重复已完成的操作。
```

## system_hint 的位置说明

`system_hint` 在当前项目主要出现在工具输出截断场景（`truncateOutput` 返回值中），作用是告诉模型“结果被截断，需要分段读取”。

它和系统提示词是两条链路：
- 系统提示词：全局行为约束
- 工具返回里的 `system_hint`：局部调用语义提示

## 设计收益

这套两段式结构的目标是：

- 保持静态提示词可读、可维护
- 在不修改静态文件的前提下注入临时状态
- 让提示词内容和工具 schema 的职责边界清晰
