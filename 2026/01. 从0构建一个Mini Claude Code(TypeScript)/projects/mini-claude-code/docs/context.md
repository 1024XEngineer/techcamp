# 上下文管理

## 问题背景

ReAct 循环会持续把消息追加到 `history`：用户输入、模型中间步骤、工具调用与工具结果。任务越长，上下文越大，最终会逼近模型窗口上限。

`mini-claude-code` 当前实现采用：

**真实 token 计数 → 阈值判断 → 历史压缩 → 会话提示重建**

## 计数来源：SDK usage.promptTokens

当前代码不做字符估算，而是直接使用 Vercel AI SDK 返回的真实统计值：

```typescript
// src/agent/context.ts
const MODEL_CONTEXT_LIMIT = 128_000
const COMPRESS_THRESHOLD = 0.8

export function shouldCompress(promptTokens: number): boolean {
  return promptTokens > MODEL_CONTEXT_LIMIT * COMPRESS_THRESHOLD
}
```

即：当 `promptTokens > 102400` 时触发压缩。

## 触发时机

触发点在 `src/index.ts` 的“每轮结束后”：

```typescript
const { text, responseMessages, usage } = await agentLoop(...)

history.push({ role: 'user', content: question })
history.push(...responseMessages)

if (shouldCompress(usage.promptTokens)) {
  const summary = await compressHistory(history)
  const hint = buildCompressionHint(summary)
  history = []
  runtimeHints = [hint]
}
```

注意：
- 不是“每步 onStepFinish 检查”
- 也不会中断 `generateText` 后递归重跑
- 是在本轮完成后再决定是否压缩

## 压缩实现

`src/agent/context.ts` 会把完整历史拼成文本，让模型生成结构化摘要：

```typescript
const COMPRESS_SYSTEM = `
你是一个 Agent 执行历史压缩器。将以下执行历史总结为结构化摘要，输出格式如下（使用 XML 标签）：

<completed>...</completed>
<remaining>...</remaining>
<current_state>...</current_state>
<notes>...</notes>
`.trim()

export async function compressHistory(history: CoreMessage[]): Promise<string> {
  const historyText = history
    .map((m) => {
      const content = typeof m.content === 'string' ? m.content : JSON.stringify(m.content)
      return `[${m.role}]\n${content}`
    })
    .join('\n\n---\n\n')

  const { text } = await generateText({
    model,
    system: COMPRESS_SYSTEM,
    prompt: historyText,
    maxSteps: 1,
  })

  return text
}
```

## 会话重建方式

压缩后不保留旧 `history`，而是：

1. 清空历史：`history = []`
2. 生成运行时提示：`buildCompressionHint(summary)`
3. 把提示写入 `runtimeHints`

`agentLoop` 下轮调用时会把 `runtimeHints` 注入系统提示词（见 `src/agent/prompt.ts`）。

```typescript
export function buildCompressionHint(summary: string): string {
  return [
    '[执行历史摘要 - 之前会话已压缩]',
    '',
    summary,
    '',
    '注意：以上是对之前执行历史的摘要，你处于重建会话状态。',
    '请基于摘要继续完成原始任务，不要重复已完成的操作。',
  ].join('\n')
}
```

## 流程图

```text
本轮用户输入
    │
    ▼
agentLoop(question, history, runtimeHints)
    │
    ▼
返回 { text, responseMessages, usage.promptTokens }
    │
    ├── 追加到 history
    │
    └── shouldCompress(promptTokens) ?
            │
         是 │
            ▼
      compressHistory(history)
            │
            ▼
      runtimeHints = [buildCompressionHint(summary)]
      history = []
```

## 与工具截断的关系

工具输出截断（`utils/truncate.ts`）是第一道防线，尽量减少单次输出造成的 token 峰值；历史压缩是第二道防线，处理长任务累积上下文。

两者配合，才能在真实的多步任务里保持会话可持续。
