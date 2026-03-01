# 安全设计

## 为什么 Agent 需要安全机制

Agent 能执行 Shell 命令、读写本地文件，风险明显高于只输出文本的聊天机器人。`mini-claude-code` 当前实现提供三层基础防护：

1. `bash` 的危险命令分级检测
2. 文件工具的路径越界检查
3. 敏感路径告警与输出长度控制

## 第一道：危险命令检测（bash）

`src/utils/safety.ts` 的命令分级如下：

```typescript
export type DangerLevel = 'safe' | 'confirm' | 'block'

const BLOCK_PATTERNS: RegExp[] = [
  /rm\s+-\S*r\S*f\s+(\/|~|\$HOME)\b/,
  /dd\s+if=.*of=\/dev\//,
  /mkfs\./,
  />\s*\/dev\/(sda|hda|nvme)/,
  /shutdown|reboot|halt/,
]

const CONFIRM_PATTERNS: RegExp[] = [
  /rm\s+-\S*[rf]/,
  /sudo\s+/,
  /curl\s+.*\|\s*(sh|bash|zsh)/,
  /wget\s+.*\|\s*(sh|bash|zsh)/,
  /npm\s+publish/,
  /git\s+push\s+.*--force/,
  /git\s+reset\s+--hard/,
]
```

执行策略：
- `block`：直接拒绝执行
- `confirm`：暂停并询问用户
- `safe`：直接执行

确认交互来自 `src/utils/confirm.ts`，只有用户输入 `y` 才视为同意。

## 第二道：路径安全（read/write/edit）

`src/utils/safety.ts` 会把输入路径解析到绝对路径，并确保仍位于当前工作目录内：

```typescript
export function resolveSafePath(inputPath: string): string {
  const cwd = process.cwd()
  const resolved = resolve(cwd, inputPath)

  if (!resolved.startsWith(cwd + '/') && resolved !== cwd) {
    throw new Error(`路径越界：${inputPath} 解析为 ${resolved}，超出工作目录 ${cwd}`)
  }

  return resolved
}
```

这可以阻止典型路径穿越，如 `../../etc/passwd`。

## 第三道：敏感路径告警 + 输出截断

### 1) 敏感文件访问告警

`read_file` 会对以下路径模式给出警告（不强制阻断）：

```typescript
const SENSITIVE_PATTERNS: RegExp[] = [
  /\.env(\.|$)/,
  /\.aws\/credentials/,
  /\.ssh\/(id_rsa|id_ed25519)$/,
  /secrets?\.(json|yaml|yml)$/i,
]
```

### 2) 工具输出截断

`src/utils/truncate.ts` 限制单次工具输出最大 8000 字符，超出时追加结构化 `system_hint`，避免上下文被单次工具结果冲垮。

## 局限与边界

当前方案是教学场景下的“最小安全集”，不是生产级沙箱：

- 命令检测基于正则，无法覆盖所有变体
- 工具在本地环境执行，不是容器隔离
- 敏感路径目前以“告警”为主，不做强制拒绝

如果要用于生产，通常还需要容器隔离、权限分级、审计日志和更严格的命令策略。
