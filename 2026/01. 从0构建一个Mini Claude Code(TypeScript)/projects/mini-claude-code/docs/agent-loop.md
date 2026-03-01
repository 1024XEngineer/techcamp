# Agent Loop 设计

## 从 agent-loop 到 mini-claude-code

`projects/agent-loop` 手写了完整循环：手动请求模型、手动解析 XML、手动回填 observation。

`mini-claude-code` 的实现改成 Vercel AI SDK 的 `generateText + tools + maxSteps`，把工具调用状态机交给 SDK：

```typescript
const result = await generateText({
  model,
  system,
  messages,
  tools: TOOLS,
  maxSteps: 50,
  onStepFinish,
})
```

## 实际调用结构

`src/agent/loop.ts` 当前封装如下：

```typescript
export async function agentLoop(question, history, runtimeHints = []) {
  const system = await assembleSystemPrompt(runtimeHints)

  const messages = [
    ...history,
    { role: 'user', content: question },
  ]

  const result = await generateText({
    model,
    system,
    messages,
    tools: TOOLS,
    maxSteps: 50,
    onStepFinish: ({ text, toolCalls, finishReason }) => {
      const isFinalStep = finishReason === 'stop' && toolCalls.length === 0
      if (!isFinalStep) {
        printStep({ text, toolCalls, finishReason })
      }
    },
  })

  return {
    text: result.text,
    responseMessages: result.response.messages,
    usage: result.usage,
    stepCount: result.steps.length,
  }
}
```

要点：
- `messages` 由 `history + 本轮 user 输入`组成
- `maxSteps=50` 防止无限循环
- `onStepFinish` 只负责过程打印，不做上下文压缩判断
- `usage.promptTokens` 在外层 CLI（`src/index.ts`）用于压缩判断

## onStepFinish 的职责

当前实现只有两件事：

1. 打印中间步骤
2. 跳过最终自然结束的那一步（避免和最终回答重复）

打印格式示例：

```text
── Step 1 ──────────────────────────────────
我先读取 package.json 看脚本配置。

🔧 read_file {"path":"package.json"}
```

如果总步数大于 1，会额外打印：

```text
[共执行 N 步]
```

## Provider 配置（七牛 OpenAI 兼容接口）

`src/agent/provider.ts` 使用 `createOpenAI`：

```typescript
const qiniu = createOpenAI({
  apiKey: process.env.QINIU_API_KEY,
  baseURL: 'https://api.qnaigc.com/v1',
  compatibility: 'compatible',
})

const modelName = process.env.QINIU_MODEL ?? 'claude-4.6-sonnet'
export const model = qiniu(modelName)
```

`compatibility: "compatible"` 的目的是适配非 OpenAI 官方端点，避免发送不兼容字段（例如部分服务不支持的角色格式）。

## 多轮对话下的消息管理

在 `src/index.ts` 中，单轮执行完成后会把本轮内容追加到 `history`：

```typescript
history.push({ role: 'user', content: question })
history.push(...responseMessages)
```

`responseMessages` 包含中间工具调用轨迹，下一轮会携带这些上下文继续推理。

## 与 Context 模块的边界

`agentLoop` 负责“本轮执行”，不负责压缩。

上下文压缩在 `index.ts` 中进行：

1. `agentLoop(...)` 返回 `usage.promptTokens`
2. `shouldCompress(usage.promptTokens)` 判断是否超阈值
3. 超阈值时调用 `compressHistory(history)`
4. `history = []`，并把摘要放入 `runtimeHints`

这保证了 loop 模块职责单一，CLI 负责会话生命周期。

## 错误处理

| 错误类型 | 当前处理方式 |
|---------|-------------|
| LLM API 调用失败 | `index.ts` 捕获异常并打印 `[错误]` |
| 工具执行异常 | 工具函数返回错误字符串给模型，模型可自行调整下一步 |
| 用户拒绝危险命令 | `bash` 返回“用户拒绝执行命令”，模型改走替代方案 |
| 上下文压缩失败 | 仅告警 `[压缩失败: ...]`，保留原会话继续 |
