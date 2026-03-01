# 整体架构

## 架构图

```bash
┌─────────────────────────────────────────────────────────────┐
│                      mini-claude-code                      │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  UI Layer — CLI                                     │    │
│  │                                                     │    │
│  │  readline 多轮对话 → 接收用户输入 → 打印执行过程       │    │
│  └──────────────────────────┬──────────────────────────┘    │
│                             │ question                      │
│                             ▼                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Agent Layer                                        │    │
│  │                                                     │    │
│  │  ┌───────────────────────────────────────────────┐  │    │
│  │  │  Prompt Assembler                             │  │    │
│  │  │  静态提示词 + 运行时状态(runtimeHints)         │  │    │
│  │  └───────────────────────────────────────────────┘  │    │
│  │                                                     │    │
│  │  ┌───────────────────────────────────────────────┐  │    │
│  │  │  AgentLoop (generateText + maxSteps=50)       │  │    │
│  │  │                                               │  │    │
│  │  │  Observe → Think → Act → Observe → ...       │  │    │
│  │  │                                               │  │    │
│  │  │  onStepFinish: 打印步骤与工具调用              │  │    │
│  │  └───────────────────────────────────────────────┘  │    │
│  │                                                     │    │
│  │  ┌───────────────────────────────────────────────┐  │    │
│  │  │  Context Manager                              │  │    │
│  │  │  每轮结束后基于 usage.promptTokens 判断是否压缩 │  │    │
│  │  └───────────────────────────────────────────────┘  │    │
│  └──────────────────────────┬──────────────────────────┘    │
│                             │ tool calls                    │
│                             ▼                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Tools Layer                                        │    │
│  │                                                     │    │
│  │  read_file   write_file   edit_file                 │    │
│  │  bash        web_fetch                              │    │
│  │                                                     │    │
│  │  ┌───────────────────────────────────────────────┐  │    │
│  │  │  Safety Guard                                 │  │    │
│  │  │  危险命令检测 → 用户审批 → 执行 / 取消         │  │    │
│  │  └───────────────────────────────────────────────┘  │    │
│  │                                                     │    │
│  │  ┌───────────────────────────────────────────────┐  │    │
│  │  │  Output Truncator                             │  │    │
│  │  │  超限时截断 → 注入 system_hint                │  │    │
│  │  └───────────────────────────────────────────────┘  │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

## 层级说明

### UI Layer

负责与用户交互，保持多轮对话会话。具体职责：

- 启动 readline 交互
- 接收用户问题，传入 Agent Layer
- 实时展示 Agent 每步的思考和行动
- 支持 `/exit`、`/reset`、`/help` 等 slash 命令

### Agent Layer

核心业务逻辑。包含三个组件：

**AgentLoop**：基于 Vercel AI SDK 的 `generateText`，设置 `maxSteps=50` 实现 ReAct 循环。每步通过 `onStepFinish` 回调打印进度（教学用）。

**Prompt Assembler**：将静态系统提示词（`SYSTEM_PROMPT.md`）和运行时状态（例如压缩摘要）拼装成最终系统提示词。

**Context Manager**：在每轮对话结束后使用 SDK 返回的真实 `usage.promptTokens` 判断上下文用量。超过阈值时执行压缩并重置会话状态。

### Tools Layer

提供 5 个核心工具，每个工具都经过两道防护：

- **Safety Guard**（主要在 `bash` 中生效）：危险命令检测 + 用户审批
- **Output Truncator**（`read_file`/`bash`/`web_fetch` 等）：超过字符阈值时截断并附加 `system_hint`

## 数据流

```text
用户输入
    │
    ▼
index.ts
    │
    ├── resetStepCounter()
    │
    ├── agentLoop(question, history, runtimeHints)
    │       │
    │       ├── assembleSystemPrompt(runtimeHints)
    │       │
    │       ├── messages = [...history, { role: 'user', content: question }]
    │       │
    │       └── generateText({ system, messages, tools, maxSteps: 50, onStepFinish })
    │
    ├── history.push({ role: 'user', content: question })
    ├── history.push(...responseMessages)
    │
    └── shouldCompress(usage.promptTokens) ?
            │
         是 │
            ▼
      summary = compressHistory(history)
      runtimeHints = [buildCompressionHint(summary)]
      history = []
```

## 文件结构

```text
projects/mini-claude-code/
├── src/
│   ├── index.ts
│   ├── SYSTEM_PROMPT.md
│   ├── agent/
│   │   ├── provider.ts
│   │   ├── loop.ts
│   │   ├── context.ts
│   │   └── prompt.ts
│   ├── tools/
│   │   ├── index.ts
│   │   ├── read-file.ts
│   │   ├── write-file.ts
│   │   ├── edit-file.ts
│   │   ├── bash.ts
│   │   └── web-fetch.ts
│   └── utils/
│       ├── truncate.ts
│       ├── safety.ts
│       └── confirm.ts
├── docs/
├── package.json
├── tsconfig.json
└── .env.example
```

## 与 agent-loop 的对比

| 维度 | agent-loop | mini-claude-code |
|------|-----------|-----------------|
| LLM 调用 | 原生 fetch | Vercel AI SDK `generateText` |
| 工具协议 | 手写 XML | SDK 原生 tool calling（JSON schema） |
| 循环控制 | 手写 `for` + 手写解析 | `maxSteps` 参数 |
| 工具类型 | 模拟（天气、时间） | 真实（文件、Shell、网络） |
| 上下文管理 | 无 | `usage.promptTokens` + 压缩摘要 |
| 安全机制 | 无 | 危险命令检测 + 审批 |
| 输出保护 | 无 | 截断 + `system_hint` |
| 多模型支持 | 需手改代码 | Provider 配置切换 |
