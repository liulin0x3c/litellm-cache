# litellm-cache

> **This is a demo project.** It demonstrates a minimal approach to the idea described below. Feel free to fork, adapt, or use it as a starting point for your own implementation.

> **本项目是一个 demo。** 旨在演示下述思路的最小可用实现，欢迎 fork、改造，或以此为起点构建你自己的方案。

---

## English

A thin wrapper around LiteLLM with a built-in file-system request cache. One `chat()` call covers 100+ LLM providers; two extra parameters give any long-running pipeline a save/load-style checkpoint mechanism.

### The idea

Multi-step LLM pipelines (agents, batch jobs, complex chains) share two pain points:

**Debugging is expensive and flaky.** When step N fails, re-running steps 1 through N-1 costs real money and time — and because LLM outputs are non-deterministic, the bug you saw last time might not even show up again.

**You can't pause and resume.** Want to stop halfway to inspect intermediate results, or re-run only the second half with new logic? Too bad — you start from scratch.

This project offers a straightforward fix: **hash the request parameters to a local JSON file; identical requests return the cached result instantly.** Your pipeline gains save/load semantics — stop anytime, resume from where you left off, and get fully deterministic outputs during debugging.

### What it does

- **Unified LLM interface** — Powered by LiteLLM. A single `chat()` method covers OpenAI, Anthropic, DeepSeek, and 100+ other providers. Switching providers means changing one `model` string.
- **Request-level file cache** — SHA-256 hash of `model + messages + params` as filename, organized by `cache_index` subdirectories. Cache toggle and batch label are just parameters on `chat()` — zero changes to your business logic.
- **Human-readable cache files** — Each cache entry is a formatted JSON containing the full request, the full response, and a timestamp. Open it, read it, understand it.
- **Decoupled cache layer** — `FileCache` is a standalone module with no dependency on `MultiProviderClient`. Use it anywhere you need local caching.

### Install

```bash
pip install -e /path/to/litellm_with_cahce    # editable install for development
pip install /path/to/litellm_with_cahce        # or direct install
```

### Environment variables

Set API keys for the providers you use. LiteLLM picks them up automatically:

```bash
export OPENAI_API_KEY="..."
export DEEPSEEK_API_KEY="..."
export ANTHROPIC_API_KEY="..."
```

### Usage

```python
from litellm_cache import MultiProviderClient, build_message

client = MultiProviderClient(default_model="openai/gpt-4o")

# Basic call
resp = client.chat(messages=[build_message("user", "Hello")])

# Switch provider — just change the model string
resp = client.chat(model="deepseek/deepseek-chat", messages=[...])

# Enable cache — add two parameters
resp = client.chat(
    messages=[build_message("user", "Analyze this code...")],
    use_debug_cache=True,
    cache_index="debug_0309",
)
```

Long-running pipeline:

```python
for task in tasks:
    result = client.chat(
        messages=[build_message("user", task)],
        use_debug_cache=True,
        cache_index="pipeline_v1",
    )
    process(result)
```

Ctrl+C halfway through. Next run skips all cached steps and picks up where it stopped. Changed your prompts? Use `cache_index="pipeline_v2"` — old cache stays untouched.

### Cache file structure

Path: `.cache/{cache_index}/{hash}.json`

```json
{
  "request": {
    "model": "openai/gpt-4o",
    "messages": [{"role": "user", "content": "Analyze this code..."}],
    "stream": false,
    "kwargs": {}
  },
  "response": {
    "id": "chatcmpl-xxx",
    "choices": [{"message": {"role": "assistant", "content": "..."}}],
    "usage": {"prompt_tokens": 10, "completion_tokens": 50}
  },
  "cached_at": "2026-03-09T12:00:00+00:00"
}
```

### Limitations

- Cache only works with `stream=False`. Streaming responses are not cached.
- Cache matching is strict hash-based — any change in parameters (message content, order, model name) is treated as a new request.
- No automatic expiration or eviction. Delete `.cache/` subdirectories manually to clean up.

---

## 中文

对 LiteLLM 的轻量封装，内置基于文件系统的请求级缓存。一个 `chat()` 方法覆盖 100+ 模型供应商，两个额外参数让任何长流程具备存档/读档能力。

### 思路

涉及多次 LLM 调用的长流程（多步 Agent、批量处理、复杂 pipeline）有两个绕不开的麻烦：

**调试成本高且不稳定。** 流程跑到第 N 步出问题，重跑前 N-1 步要花真金白银，而且 LLM 输出有随机性——上次能复现的 bug 下次未必还在。

**没法中途停下来。** 想暂停看中间状态？想只改后半段逻辑？一旦中断就只能从头来过。

本项目的办法很朴素：**把请求参数做 hash 映射到本地 JSON 文件，相同请求直接返回缓存结果。** 长流程因此获得存档/读档能力——随时停、随时续、调试时结果完全确定。

### 它做了什么

- **统一调用接口** —— 基于 LiteLLM，一个 `chat()` 方法覆盖 OpenAI、Anthropic、DeepSeek 等 100+ 供应商，切换只需改 `model` 字符串。
- **请求级文件缓存** —— 以 `model + messages + 其他参数` 的 SHA-256 哈希作为文件名，按 `cache_index` 分目录存储。缓存开关和批次标识直接作为 `chat()` 的参数传入，零侵入。
- **缓存对人友好** —— 每个缓存文件是格式化的 JSON，包含完整的请求参数、响应内容和写入时间，直接打开就能看懂。
- **缓存层独立** —— `FileCache` 不依赖 `MultiProviderClient`，可以单独引入到任何需要做本地缓存的场景。

### 安装

```bash
pip install -e /path/to/litellm_with_cahce    # 可编辑安装，适合开发
pip install /path/to/litellm_with_cahce        # 或直接安装
```

### 环境变量

设置你要用的供应商的 API Key，LiteLLM 会自动读取：

```bash
export OPENAI_API_KEY="..."
export DEEPSEEK_API_KEY="..."
export ANTHROPIC_API_KEY="..."
```

### 使用

```python
from litellm_cache import MultiProviderClient, build_message

client = MultiProviderClient(default_model="openai/gpt-4o")

# 基本调用
resp = client.chat(messages=[build_message("user", "你好")])

# 换供应商只改 model
resp = client.chat(model="deepseek/deepseek-chat", messages=[...])

# 启用缓存——加两个参数
resp = client.chat(
    messages=[build_message("user", "分析这段代码...")],
    use_debug_cache=True,
    cache_index="debug_0309",
)
```

长流程场景：

```python
for task in tasks:
    result = client.chat(
        messages=[build_message("user", task)],
        use_debug_cache=True,
        cache_index="pipeline_v1",
    )
    process(result)
```

跑到一半 Ctrl+C，下次重启自动跳过已缓存的步骤，从断点继续。改了 prompt 策略？换个 `cache_index="pipeline_v2"` 即可，旧缓存不受影响。

### 缓存文件结构

存储路径：`.cache/{cache_index}/{hash}.json`

```json
{
  "request": {
    "model": "openai/gpt-4o",
    "messages": [{"role": "user", "content": "分析这段代码..."}],
    "stream": false,
    "kwargs": {}
  },
  "response": {
    "id": "chatcmpl-xxx",
    "choices": [{"message": {"role": "assistant", "content": "..."}}],
    "usage": {"prompt_tokens": 10, "completion_tokens": 50}
  },
  "cached_at": "2026-03-09T12:00:00+00:00"
}
```

### 局限

- 仅在 `stream=False` 时缓存，流式输出不缓存。
- 缓存匹配基于参数的严格哈希，参数有任何变化（包括 message 内容、顺序、model 名称）都会视为新请求。
- 不做缓存过期和淘汰，需要手动删除 `.cache/` 下的目录或文件来清理。
