# Agent Loop 设计

## 从 agent-loop 到 mini-claude-code

`agent-loop` 项目手写了整个循环：

```typescript
// agent-loop 的做法
for (let step = 0; step < 10; step++) {
  const text = await callLLMs(history)          // 原生 fetch
  const parsed = parseAssistant(text)            // 手写正则解析 XML
  if (parsed.final) return parsed.final
  if (parsed.action) {
    const result = await executeTool(parsed.action)
    history.push({ role: 'user', content: `<observation>${result}</observation>` })
  }
}
```

`mini-claude-code` 用 Vercel AI SDK 替代手写部分：

```typescript
// mini-claude-code 的做法
const result = await generateText({
  model: provider('model-name'),
  system: await assembleSystemPrompt(),
  messages: history,
  tools: TOOLS,              // SDK 自动处理工具调用状态机
  maxSteps: 20,             // SDK 自动循环，直到 LLM 停止调用工具
  onStepFinish: callback,   // 每步回调：打印执行步骤（教学用）
})
```

SDK 帮我们做掉了：工具调用的 JSON 解析、`tool_result` 的回填、循环控制。

## generateText 参数详解

```typescript
import { generateText } from 'ai'

const { text, steps } = await generateText({
  // 模型：七牛 Provider（OpenAI 兼容），默认使用 claude-4.6-sonnet
  model: qiniu(process.env.QINIU_MODEL ?? 'claude-4.6-sonnet'),

  // 系统提示词：每次对话组装一次
  system: await assembleSystemPrompt(runtimeHints),

  // 历史消息：维护在 AgentLoop 外部，支持多轮对话
  messages: history,

  // 工具注册：从 tools/index.ts 导入
  tools: TOOLS,

  // 最大步数：防止无限循环，50 步支持较长任务
  maxSteps: 50,

  // 每步完成的回调（仅用于打印教学输出）
  onStepFinish: ({ text, toolCalls, finishReason }) => {
    const isFinalStep = finishReason === 'stop' && toolCalls.length === 0
    if (!isFinalStep) {
      printStep(text, toolCalls, finishReason)
    }
  },
})
```

## ReAct 循环可视化

SDK 的 `maxSteps` 背后，就是我们在 `agent-loop` 里手写的 ReAct 循环：

```
第 1 步
  LLM 输出: "我需要先读取 package.json 来了解项目结构"
  Tool Call: read_file({ path: 'package.json' })
  Tool Result: '{"name": "my-app", "scripts": {...}}'

第 2 步
  LLM 输出: "项目使用 Vite，我来看一下 vite.config.ts"
  Tool Call: read_file({ path: 'vite.config.ts' })
  Tool Result: [文件内容]

第 3 步
  LLM 输出: "找到问题了，需要修改第 12 行的配置"
  Tool Call: edit_file({ path: 'vite.config.ts', old: '...', new: '...' })
  Tool Result: 'success'

第 4 步（无工具调用）
  LLM 输出: "我已经修改了 vite.config.ts 的第 12 行..."
  finishReason: 'stop'  → 循环结束
```

## onStepFinish 回调的职责

这个回调负责打印每步的执行过程（教学用输出），让学员看到 Agent 在干什么：

```
── Step 1 ──────────────────────────────────
🔧 read_file {"path":"package.json"}

── Step 2 ──────────────────────────────────
🔧 edit_file {"path":"src/index.ts","old_string":"...","new_string":"..."}

[共执行 3 步]
```

最后一步（无工具调用、`finishReason=stop`）不打印，由外层统一输出最终回答，避免重复显示。

> **上下文检查在哪里？** 上下文压缩检查不在 `onStepFinish` 中进行，而是在 `generateText` 返回后，由 `src/index.ts` 根据 `usage.promptTokens` 判断（见 [context.md](./context.md)）。

## 七牛 Provider 配置

七牛大模型服务兼容 OpenAI 协议，可以直接用 `@ai-sdk/openai` 的 `createOpenAI` 创建自定义 Provider：

```typescript
// agent/provider.ts
import { createOpenAI } from '@ai-sdk/openai'

export const qiniu = createOpenAI({
  apiKey: process.env.QINIU_API_KEY,
  baseURL: 'https://api.qnaigc.com/v1',  // 七牛推理服务端点
  compatibility: 'compatible',  // 兼容非官方 OpenAI 服务
})

// 使用时，默认模型 claude-4.6-sonnet，可通过 QINIU_MODEL 环境变量覆盖
const model = qiniu(process.env.QINIU_MODEL ?? 'claude-4.6-sonnet')
```

换模型只需改环境变量 `QINIU_MODEL`，换成 `qwen-max-latest` 或其他七牛支持的模型都行。

## 多轮对话的 history 管理

`generateText` 每次调用后，需要将本轮的消息追加到 `history`，供下一轮对话使用。SDK 提供了 `responseMessages` 字段：

```typescript
// index.ts（CLI 多轮对话）
const history: CoreMessage[] = []

async function chat(userInput: string) {
  const result = await agentLoop.run(userInput, history)

  // 追加本轮消息（包含所有中间步骤的 tool_call 和 tool_result）
  history.push(...result.responseMessages)
}
```

这样 history 里就包含了完整的执行轨迹，下一轮 LLM 能看到之前做了什么。

## 错误处理

| 错误类型 | 处理方式 |
|---------|---------|
| LLM API 调用失败 | 捕获后告知用户，不崩溃 |
| 工具执行异常 | 将错误信息作为 tool_result 返回给 LLM，让它自修正 |
| maxSteps 用尽 | 提示用户任务未完成，可继续追问 |
| 上下文接近上限 | `generateText` 返回后检查 `usage.promptTokens`，超阈值时压缩历史（见 context.md） |
| 用户拒绝危险命令 | 将"用户拒绝"作为 tool_result 返回，LLM 会调整策略 |
