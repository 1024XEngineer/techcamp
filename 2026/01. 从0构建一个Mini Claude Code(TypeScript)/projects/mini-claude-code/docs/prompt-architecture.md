# 系统提示词架构

## 问题：提示词不只是一个文件

简单的 Agent 把系统提示词写死在代码或一个 `.md` 文件里。但在 `mini-claude-code` 中，系统提示词需要包含**不同来源、不同性质**的内容：

| 内容类型 | 来源 | 特点 |
|---------|------|------|
| 基础行为指令 | `SYSTEM_PROMPT.md` 静态文件 | 固定，不变 |
| 运行时状态 | 执行过程中动态注入 | 每次请求可能不同 |

这就需要一套**组装逻辑**，而不是一个静态字符串。

## 提示词结构

最终发送给 LLM 的系统提示词由两个段落拼接：

```
┌─────────────────────────────────────────────────────┐
│  Segment 1: 核心指令（静态）                          │
│  来源：SYSTEM_PROMPT.md                              │
│  内容：角色定义、行为准则、工具使用建议、输出格式要求  │
├─────────────────────────────────────────────────────┤
│  Segment 2: 运行时状态（动态，可选）                  │
│  来源：执行过程中注入                                 │
│  内容：上下文压缩摘要、异常提示、特殊约束             │
└─────────────────────────────────────────────────────┘
```

> 注：工具参数 schema 由 Vercel AI SDK 自动注入到 function calling，不需要在系统提示词中重复描述。工具的**使用策略**（何时用、注意事项）已包含在 `SYSTEM_PROMPT.md` 的「工具使用建议」部分。

## SYSTEM_PROMPT.md（静态段）

```markdown
# 角色

你是 mini-claude-code，一个运行在用户本地终端的 Code Agent。你可以读写文件、执行 Shell 命令、访问网络，帮助用户完成代码开发任务。

# 行为准则

1. **先理解，再行动**：在执行任何修改前，先读取相关文件，确认你理解了上下文。
2. **最小化操作**：只修改完成任务所必需的内容，不引入无关改动。
3. **及时汇报**：每次工具调用后，说明你做了什么，发现了什么。
4. **遇到不确定，停下来问**：不要猜测用户意图，不确定时直接提问。

# 输出规范

- 使用中文与用户交流
- 代码块使用对应语言的语法高亮
- 任务完成后给出简洁的总结，说明做了哪些修改

# 工具使用建议

- 修改文件前，先用 read_file 读取内容，确认目标位置
- 对大文件，用 read_file 的 offset/limit 参数分段读取，不要一次读全量
- 优先用 edit_file 做局部修改，只在需要完整重写时用 write_file
- bash 命令执行前，确认命令的影响范围
```

## 组装逻辑

```typescript
// agent/prompt.ts

export async function assembleSystemPrompt(
  runtimeHints: string[] = []
): Promise<string> {
  const segments: string[] = []

  // Segment 1: 静态核心指令
  segments.push(await Bun.file(PROMPT_FILE).text())

  // Segment 2: 运行时状态（如有）
  if (runtimeHints.length > 0) {
    segments.push("---\n# 运行时状态\n\n" + runtimeHints.join("\n\n"))
  }

  return segments.join("\n\n")
}
```

## 运行时状态注入

某些特殊情况需要在系统提示词中动态插入状态说明：

### 上下文压缩后的摘要注入

```typescript
// 压缩完成后，将摘要作为运行时 hint 注入
const hint = buildCompressionHint(summary)
runtimeHints = [hint]

// 下次调用 agentLoop 时，hint 会作为 Segment 2 注入系统提示词
```

### 工具异常状态注入

如果某个工具出现持续异常，可以注入提示：

```typescript
const hint = `<system_hint type="tool_degraded" tool="web_fetch">
  web_fetch 工具当前不可用（网络连接问题），请避免使用该工具。
</system_hint>`
```

## system_hint 在提示词中的位置

`system_hint` 有两种使用场景，位置不同：

| 场景 | 位置 | 原因 |
|------|------|------|
| 工具输出超限 | 工具返回值中（作为 tool_result） | 直接跟随工具调用，模型立刻知道结果被截断 |
| 工具不可用、全局状态 | 系统提示词 Segment 2 | 影响全局行为，放在系统提示词层面更合适 |

## 提示词工程注意事项

### 工具描述的质量直接影响模型行为

Vercel AI SDK 自动生成的工具 schema 会注入到 function calling，模型会读取这些描述来决定何时调用工具。`tool()` 中的 `description` 要写清楚：

```typescript
// 差：太模糊
description: '读取文件'

// 好：包含何时用、有什么限制
description: '读取本地文件的内容。对于大文件，建议使用 offset 和 limit 参数分段读取，而不是一次性读取全量内容。'
```

### 避免在静态提示词中写死工具参数格式

工具参数格式由 Zod schema 自动生成，在静态提示词里重复描述参数格式会导致不一致（代码改了但提示词没改）。静态提示词只写**使用策略**，不写**参数格式**。

### 提示词分段用 `---` 分隔线

各段之间用 Markdown 分隔线（`---`）和 `#` 标题区分，帮助模型识别不同来源的指令，也方便开发者调试时快速定位各段内容。
