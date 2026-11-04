# Do I need MCP to use AgentFEM?

**No. If your AI assistant can run terminal commands, start with the AgentFEM CLI.** MCP is an optional connection for compatible clients, not a prerequisite for simulation.

| Your starting point | Use |
|---|---|
| An AI assistant with terminal access | The AgentFEM CLI in your scientific environment |
| A desktop client that supports local MCP tools | AgentFEM MCP, connected to the same installed runtime |
| Custom models or repeated parameter studies | The AgentFEM Python API and CLI; add MCP only if your client needs it |

## What MCP adds

The adapter exposes seven typed tools: discover the runtime, create a template project, check it, inspect it, launch a run, monitor the job, and read the results. It manages background-run identities and restricts project paths to configured roots. Your client gets structured results without having to construct each CLI invocation.

It does **not** install the numerical runtime, improve solver accuracy, or replace Python model editing. Scientific projects contain executable Python: review unfamiliar projects before running them. An approved project folder is not a sandbox for arbitrary model code.

A **skill** is different again: it gives the assistant workflow instructions, such as checking units and comparing against a reference solution. It can accompany either CLI or MCP use.

## Try one complete simulation

1. [Install AgentFEM](https://github.com/haoming-luo/agentfem/blob/main/INSTALL.md) and confirm that `agentfem doctor` succeeds.
2. Follow the [AI-assisted cantilever example](https://haoming-luo.github.io/agentfem/examples/ai_assisted_fem/). Keep the model, result files, and comparison with beam theory.
3. If your client needs MCP, use the [connection instructions](../README.md#bring-it-to-life).

Just exploring? The [browser lab](https://lab.haoming-luo.com/structural-design/) needs no installation. It compares precomputed candidates; it does not run a new finite-element solve in your browser.

---

## 使用 AgentFEM，一定要配置 MCP 吗？

**不需要。AI 助手能运行终端命令，就可以直接使用 AgentFEM 的命令行工具。** 已经能算的，不必再换一套连接方式。

- **终端里的 AI 助手：**直接使用 CLI。
- **支持本地 MCP 的桌面客户端：**用 MCP 连接已经安装好的 AgentFEM。
- **自定义模型、批量计算：**使用 Python API 和 CLI，按需接入 MCP。

MCP 把建项目、检查、运行和读取结果等操作整理成固定工具，方便客户端调用；它不替你安装求解环境，也不会改变计算精度。Skill 则是给 AI 的操作指引，两者不是一回事。

第一次使用，先完成[悬臂梁算例](https://haoming-luo.github.io/agentfem/examples/ai_assisted_fem/)，把结果与梁理论对上。想先看看效果，可以直接打开[在线案例](https://lab.haoming-luo.com/structural-design/)；其中展示的是预先计算的结果。
