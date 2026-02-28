# 上下文管理

## 问题背景

ReAct 循环的每一步都会往 `history` 里追加消息：LLM 的思考、工具调用、工具结果……任务越复杂，history 越长，迟早触碰模型的上下文长度上限。

更糟糕的是：**上下文变长不只是会报错，还会让模型开始"遗忘"**——太长的上下文里，早期的关键信息会被"稀释"，模型的表现会下降。

`mini-claude-code` 的上下文管理策略：**计数 → 预警 → 压缩 → 重建**。

## Token 计数

精确的 token 计数需要分词器，成本高且与模型绑定。`mini-claude-code` 直接使用 Vercel AI SDK 在每次 `generateText` 调用后返回的 `usage.promptTokens`，这是 API 服务端返回的真实值，比字符数估算更准确：

```typescript
// src/index.ts（每轮对话结束后检查）
const { text, responseMessages, usage, stepCount } = await agentLoop(...)

// usage.promptTokens 是本轮实际发送的 token 数，由 API 返回
if (shouldCompress(usage.promptTokens)) {
  // 触发压缩...
}
```

## 阈值设计

```typescript
// agent/context.ts

// 主流模型上下文长度（以 128k 为例）
const MODEL_CONTEXT_LIMIT = 128_000   // tokens

// 80% 时触发压缩：留 20% 给 LLM 输出和本轮工具结果
const COMPRESS_THRESHOLD = 0.8

// 接收 SDK 返回的真实 promptTokens，直接与阈值比较
export function shouldCompress(promptTokens: number): boolean {
  return promptTokens > MODEL_CONTEXT_LIMIT * COMPRESS_THRESHOLD
}
```

## 压缩流程

触发压缩后，执行以下步骤：

```
当前 history（很长）
        │
        ▼
  让 LLM 生成摘要
        │
        ▼
  摘要包含 4 部分：
    1. 已完成的任务
    2. 尚未完成的任务
    3. 当前状态（修改了哪些文件、关键发现）
    4. 注意事项（踩过的坑、边界条件）
        │
        ▼
  重建 history：
    [system] 原系统提示词 + 压缩摘要 hint
    [user]   原始用户问题（保留）
        │
        ▼
  继续执行 AgentLoop
```

### 压缩提示词

```typescript
// agent/context.ts

const COMPRESS_PROMPT = `
请对以下 Agent 执行历史进行压缩总结，输出格式如下（使用 XML 标签）：

<completed>
已完成的具体操作列表（每行一条）
</completed>

<remaining>
还未完成的任务或子任务
</remaining>

<current_state>
当前状态：已修改的文件、关键变量值、环境状态等
</current_state>

<notes>
重要注意事项：踩过的坑、特殊处理、边界条件
</notes>

要求：
- 信息密度高，不要废话
- 保留所有对后续执行有用的细节
- 忘记所有已经完成且不影响后续的步骤细节
`.trim()
```

### 压缩实现

```typescript
export async function compressHistory(
  history: CoreMessage[]
): Promise<string> {
  // 把完整 history 拼成文本交给 LLM 总结
  const historyText = history
    .map(m => {
      const content = typeof m.content === 'string'
        ? m.content
        : JSON.stringify(m.content)
      return `[${m.role}]\n${content}`
    })
    .join('\n\n---\n\n')

  const { text } = await generateText({
    model,
    system: COMPRESS_SYSTEM,
    prompt: historyText,
    maxSteps: 1,  // 只要一次输出，不循环
  })

  return text
}
```

## 重建会话

压缩完成后，用摘要重建 history。`context.ts` 提供 `buildCompressionHint` 将摘要格式化为运行时 hint，实际重建逻辑内联在 `src/index.ts` 中：

```typescript
// src/index.ts（压缩后重建）
const summary = await compressHistory(history)
const hint = buildCompressionHint(summary)

// 清空 history，将摘要注入系统提示词的运行时状态段
history = []
runtimeHints = [hint]
```

```typescript
// agent/context.ts
export function buildCompressionHint(summary: string): string {
  return [
    "[执行历史摘要 - 之前会话已压缩]",
    "",
    summary,
    "",
    "注意：以上是对之前执行历史的摘要，你处于重建会话状态。",
    "请基于摘要继续完成原始任务，不要重复已完成的操作。",
  ].join("\n")
}
```

## 完整流程图

```
agentLoop(question, history, runtimeHints)
    │
    ├── generateText({ system, messages, tools, maxSteps: 50 })
    │       │
    │       │  [循环，每步]
    │       ├── LLM 推理 → 输出文本 或 tool_call
    │       ├── onStepFinish → 打印步骤（仅用于教学输出）
    │       └── finishReason=stop → 返回 result
    │
    ├── 返回 { text, responseMessages, usage, stepCount }
    │
    └── [调用方 src/index.ts 检查 usage.promptTokens]
            │
        shouldCompress(usage.promptTokens) ?
            │
         是 │                    否
            ▼                    ▼
    compressHistory(history)    继续下一轮对话
            │
            ▼
    buildCompressionHint(summary)
            │
            ▼
    history = []
    runtimeHints = [hint]
    （下次对话时摘要注入系统提示词）
```

## 工具输出是最大的上下文"杀手"

上下文暴涨通常不是用户消息造成的，而是工具输出——一次 `read_file` 读取大文件，一次 `bash` 输出大量日志，瞬间消耗数千 token。

所以**工具输出截断**（见 [tools.md](./tools.md)）是上下文管理的第一道防线，压缩机制是第二道防线。两道防线配合，才能支撑长时间运行的任务。

## 教学提示

对于简单任务（几步就完成的），这套机制完全不会触发——上下文几千 token 远未到阈值。

它的价值在"长任务"场景：让 Agent 调试一个复杂的 Bug、重构一个模块、写一整套测试……这时上下文管理的存在与否，决定了 Agent 能不能坚持到终点。
