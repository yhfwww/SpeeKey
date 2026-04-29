# 使用 Jaeger + OpenTelemetry 监控 Pipecat 语音 Agent 指南

本指南展示了如何在 Pipecat 服务中集成 OpenTelemetry 追踪功能，使用 Jaeger 来可视化服务调用、性能指标和依赖关系，帮助您在开发中有效利用性能监控和跟踪来优化语音 Agent 系统。

## 目录

- [概述](#概述)
- [什么是 OpenTelemetry 和 Jaeger](#什么是-opentelemetry-和-jaeger)
- [快速开始](#快速开始)
- [安装依赖](#安装依赖)
- [配置详解](#配置详解)
- [代码示例](#代码示例)
- [Trace 层级结构](#trace-层级结构)
- [在 Jaeger UI 中查看追踪](#在-jaeger-ui-中查看追踪)
- [性能优化指南](#性能优化指南)
- [故障排除](#故障排除)
- [参考资料](#参考资料)

## 概述

Pipecat 通过 OpenTelemetry 提供了完整的分布式追踪功能，让你能够：

- **可视化服务调用链**：清晰展示 STT、LLM、TTS 各环节的调用关系
- **监控性能指标**：实时追踪每个服务的耗时和资源使用
- **追踪依赖关系**：理解组件间的交互模式
- **诊断性能瓶颈**：快速定位延迟来源，指导优化决策

## 什么是 OpenTelemetry 和 Jaeger

### OpenTelemetry

**OpenTelemetry** 是 Cloud Native Computing Foundation (CNCF) 主导的开源项目，提供统一的 API、SDK、工具和集成，用于采集和导出分布式系统的遥测数据（包括 traces、metrics、logs）。

**核心概念：**

| 概念 | 说明 |
|------|------|
| **Trace** | 表示一次完整的请求调用链，贯穿所有参与的服务 |
| **Span** | Trace 的基本单元，代表一个具体的操作（如 HTTP 调用、函数执行） |
| **Span Context** | 包含唯一标识（Trace ID、Span ID）和上下文信息，用于跨服务传播 |
| **Baggage** | 用户自定义的元数据（键值对），可附加到分布式上下文中进行传播 |
| **OTLP** | OpenTelemetry Protocol，用于传输遥测数据的标准协议 |

OpenTelemetry 支持多种编程语言（Python、Go、Java、Node.js 等），开发者可以通过 SDK 自动或手动注入追踪上下文，实现跨服务的端到端追踪。

### Jaeger

**Jaeger** 是由 Uber Technologies 于 2016 年开源的分布式追踪平台，后捐赠给 CNCF 成为毕业项目。它作为追踪后端系统，负责接收、存储、处理和可视化分布式追踪数据。

**核心组件：**

| 组件 | 作用 |
|------|------|
| **Collector** | 接收来自各服务的追踪数据，进行验证、索引和存储 |
| **Query** | 提供 Web UI 查询接口，检索和展示追踪数据 |
| **Agent** | 本地守护进程，监听 UDP 端口接收 spans，批量发送至 Collector |
| **Ingester** | 从 Kafka 读取数据并写入存储后端 |

**主要功能：**
- 监控和排查分布式工作流
- 识别性能瓶颈
- 追踪问题根源
- 分析服务依赖关系

### 两者关系

OpenTelemetry 和 Jaeger 是互补的：

1. **OpenTelemetry** 负责在应用程序中生成和导出追踪数据
2. **Jaeger** 负责接收、存储和可视化这些数据
3. Jaeger 原生支持 OpenTelemetry 的 OTLP 协议，可直接接收 OpenTelemetry SDK 发送的数据

```
应用程序
    │
    ├─ OpenTelemetry SDK ────────┐
    │      (生成追踪数据)          │
    │                             ▼
    │                    OTLP Protocol
    │                             │
    └─────────────────────────────► Jaeger Collector
                                        │
                                        ▼
                                Jaeger Query + UI
                                        │
                                        ▼
                                可视化追踪数据
```

## 快速开始

### 1. 启动 Jaeger 容器

您已成功部署 Jaeger 容器：

```bash
docker run -d --name jaeger \
  -p 16686:16686 \
  -p 14317:4317 \
  -p 14318:4318 \
  jaegertracing/all-in-one:latest
```

**端口说明：**
- `16686`: Jaeger UI 界面（浏览器访问）
- `14317`: OTLP gRPC 接收端（映射到容器内部 4317）
- `14318`: OTLP HTTP 接收端（映射到容器内部 4318）

> **注意**：由于您使用了端口映射 `14317:4317`，OTLP 端点应配置为 `http://localhost:14317`

### 2. 配置环境变量

创建 `.env` 文件，配置 API 密钥并启用追踪：

```env
# 启用追踪
ENABLE_TRACING=true

# OTLP 端点（指向本地 Jaeger，注意端口映射）
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:14317

# 调试时可开启控制台输出
# OTEL_CONSOLE_EXPORT=true

# 服务 API Keys
DEEPGRAM_API_KEY=your_key_here
CARTESIA_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
```

### 3. 运行示例

```bash
uv run bot.py
```

### 4. 查看追踪数据

打开浏览器访问 [http://localhost:16686](http://localhost:16686)，选择服务名（如 `pipecat-demo`）查看追踪。

## 安装依赖

使用 pip 安装核心依赖：

```bash
pip install "pipecat-ai[tracing]"
pip install opentelemetry-exporter-otlp-proto-grpc
```

或使用 uv（推荐）：

```bash
uv sync
```

> **注意**：确保只安装 gRPC 导出器。如果存在冲突，请卸载 HTTP 导出器。

## 配置详解

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `ENABLE_TRACING` | 是否启用追踪 | - |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | OTLP 导出器端点 | `http://localhost:4317` |
| `OTEL_CONSOLE_EXPORT` | 是否启用控制台输出用于调试 | - |

### 依赖配置

在 `pyproject.toml` 中定义项目依赖：

```toml
[project]
name = "pipecat-jaeger-tracing"
version = "0.1.0"
description = "A Pipecat example using Jaeger tracing"
requires-python = ">=3.11"
dependencies = [
    "pipecat-ai[daily,webrtc,websocket,silero,cartesia,deepgram,openai,tracing,runner]>=1.0.0",
    "pipecatcloud>=0.4.4",
    "opentelemetry-exporter-otlp-proto-grpc",
]
```

## 代码示例

### 完整的 bot.py

```python
# Copyright (c) 2024–2025, Daily
# SPDX-License-Identifier: BSD 2-Clause License

import os
from dotenv import load_dotenv
from loguru import logger

from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

from pipecat.adapters.schemas.function_schema import FunctionSchema
from pipecat.adapters.schemas.tools_schema import ToolsSchema
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.frames.frames import LLMRunFrame, TTSSpeakFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import (
    LLMContextAggregatorPair,
    LLMUserAggregatorParams,
)
from pipecat.runner.types import RunnerArguments
from pipecat.runner.utils import create_transport
from pipecat.services.cartesia.tts import CartesiaTTSService
from pipecat.services.deepgram.stt import DeepgramSTTService
from pipecat.services.llm_service import FunctionCallParams
from pipecat.services.openai.llm import OpenAILLMService
from pipecat.transports.base_transport import BaseTransport, TransportParams
from pipecat.transports.daily.transport import DailyParams
from pipecat.transports.websocket.fastapi import FastAPIWebsocketParams
from pipecat.utils.tracing.setup import setup_tracing

load_dotenv(override=True)

IS_TRACING_ENABLED = bool(os.getenv("ENABLE_TRACING"))

# Step 1: 初始化 OpenTelemetry，指向本地 Jaeger
if IS_TRACING_ENABLED:
    otlp_exporter = OTLPSpanExporter(
        endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317"),
        insecure=True,
    )
    setup_tracing(
        service_name="pipecat-demo",
        exporter=otlp_exporter,
        console_export=bool(os.getenv("OTEL_CONSOLE_EXPORT")),
    )
    logger.info("OpenTelemetry tracing initialized")

async def fetch_weather_from_api(params: FunctionCallParams):
    await params.result_callback({"conditions": "nice", "temperature": "75"})

transport_params = {
    "daily": lambda: DailyParams(
        audio_in_enabled=True,
        audio_out_enabled=True,
    ),
    "twilio": lambda: FastAPIWebsocketParams(
        audio_in_enabled=True,
        audio_out_enabled=True,
    ),
    "webrtc": lambda: TransportParams(
        audio_in_enabled=True,
        audio_out_enabled=True,
    ),
}

async def run_bot(transport: BaseTransport):
    logger.info(f"Starting bot")
    
    # Step 2: 创建服务
    stt = DeepgramSTTService(api_key=os.getenv("DEEPGRAM_API_KEY"))
    tts = CartesiaTTSService(
        api_key=os.getenv("CARTESIA_API_KEY"),
        settings=CartesiaTTSService.Settings(
            voice="71a7ad14-091c-4e8e-a314-022ece01c121",  # British Reading Lady
        ),
    )
    llm = OpenAILLMService(
        api_key=os.getenv("OPENAI_API_KEY"),
        settings=OpenAILLMService.Settings(
            temperature=0.5,
            system_instruction="You are a helpful LLM in a WebRTC call.",
        ),
    )
    
    llm.register_function("get_current_weather", fetch_weather_from_api)
    
    @llm.event_handler("on_function_calls_started")
    async def on_function_calls_started(service, function_calls):
        await tts.queue_frame(TTSSpeakFrame("Let me check on that."))
    
    weather_function = FunctionSchema(
        name="get_current_weather",
        description="Get the current weather",
        properties={
            "location": {
                "type": "string",
                "description": "The city and state, e.g. San Francisco, CA",
            },
            "format": {
                "type": "string",
                "enum": ["celsius", "fahrenheit"],
                "description": "The temperature unit to use.",
            },
        },
        required=["location", "format"],
    )
    
    tools = ToolsSchema(standard_tools=[weather_function])
    context = LLMContext(tools=tools)
    user_aggregator, assistant_aggregator = LLMContextAggregatorPair(
        context,
        user_params=LLMUserAggregatorParams(
            vad_analyzer=SileroVADAnalyzer(),
        ),
    )
    
    # Step 3: 构建 Pipeline
    pipeline = Pipeline(
        [
            transport.input(),
            stt,
            user_aggregator,
            llm,
            tts,
            transport.output(),
            assistant_aggregator,
        ]
    )
    
    # Step 4: 创建 PipelineTask，启用 tracing
    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            enable_metrics=True,        # 启用指标（部分服务指标必须）
            enable_usage_metrics=True,  # 启用用量统计
        ),
        enable_tracing=IS_TRACING_ENABLED,            # 启用 tracing
        enable_turn_tracking=True,                    # 启用对话轮次追踪
        # conversation_id="customer-123",             # 可选，不填则自动生成
        # additional_span_attributes={"session.id": "abc-123"}  # 可选附加属性
    )
    
    @transport.event_handler("on_client_connected")
    async def on_client_connected(transport, client):
        logger.info(f"Client connected")
        await task.queue_frames([LLMRunFrame()])
    
    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        logger.info(f"Client disconnected")
        await task.cancel()
    
    runner = PipelineRunner(handle_sigint=False)
    await runner.run(task)

async def bot(runner_args: RunnerArguments):
    """与 Pipecat Cloud 兼容的主机器人入口点。"""
    transport = await create_transport(runner_args, transport_params)
    await run_bot(transport)

if __name__ == "__main__":
    from pipecat.runner.run import main
    main()
```

### 关键配置部分

#### 1. 导入追踪相关模块

```python
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from pipecat.utils.tracing.setup import setup_tracing
```

#### 2. 初始化追踪

```python
if IS_TRACING_ENABLED:
    otlp_exporter = OTLPSpanExporter(
        endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317"),
        insecure=True,
    )
    setup_tracing(
        service_name="pipecat-demo",
        exporter=otlp_exporter,
        console_export=bool(os.getenv("OTEL_CONSOLE_EXPORT")),
    )
```

#### 3. 在 PipelineTask 中启用追踪

```python
task = PipelineTask(
    pipeline,
    params=PipelineParams(
        enable_metrics=True,        # 启用指标
        enable_usage_metrics=True,  # 启用用量统计
    ),
    enable_tracing=True,            # 启用 tracing
    enable_turn_tracking=True,      # 启用对话轮次追踪
    conversation_id="customer-123", # 可选，不填则自动生成
    additional_span_attributes={"session.id": "abc-123"}  # 可选附加属性
)
```

## Trace 层级结构

Pipecat 的 trace 按对话自然结构组织，便于分析每个环节的延迟：

```
Conversation (conversation)
├── turn
│   ├── stt_deepgramsttservice
│   ├── llm_openaillmservice
│   └── tts_cartesiattsservice
└── turn
    ├── stt_deepgramsttservice
    ├── llm_openaillmservice
    └── tts_cartesiattsservice
```

每个 span 包含：
- **STT/LLM/TTS 各服务的耗时**
- **TTFB（Time To First Byte）指标**，用于延迟分析
- **LLM token 用量**、**TTS 字符数**等使用统计

## 在 Jaeger UI 中查看追踪

打开浏览器访问 [http://localhost:16686](http://localhost:16686)：

1. **选择服务**：在 "Service" 下拉框中选择 `pipecat-demo`
2. **查询追踪**：点击 "Find Traces" 按钮
3. **分析追踪**：点击任意 trace 查看详细的调用链和耗时分布

通过 Jaeger UI，您可以：
- 查看每轮对话中各服务的耗时分布
- 识别延迟最高的环节
- 比较不同对话的性能差异
- 分析服务依赖关系

## 性能优化指南

通过 Jaeger 追踪数据，您可以有针对性地优化语音 Agent 系统：

### 1. STT 优化
- 如果 STT 耗时过长，考虑：
  - 调整 VAD 灵敏度
  - 优化音频预处理
  - 考虑使用更快的 STT 服务

### 2. LLM 优化
- 如果 LLM 响应时间过长，考虑：
  - 调整 temperature 参数
  - 使用更小的模型
  - 优化 prompt 长度
  - 启用流式响应

### 3. TTS 优化
- 如果 TTS 耗时过长，考虑：
  - 选择更轻量的语音模型
  - 启用流式 TTS
  - 优化音频编码设置

### 4. Pipeline 优化
- 分析各组件之间的等待时间
- 考虑并行处理某些步骤
- 优化数据流转效率

## Docker 部署

项目提供了 Dockerfile 用于容器化部署：

```dockerfile
FROM dailyco/pipecat-base:latest

# 启用字节码编译
ENV UV_COMPILE_BYTECODE=1

# 从缓存复制而不是链接，因为它是一个挂载的卷
ENV UV_LINK_MODE=copy

# 使用锁文件和设置安装项目依赖
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-dev

# 复制应用代码
COPY ./bot.py bot.py
```

## 故障排除

| 问题 | 解决方法 |
|------|----------|
| Jaeger 中看不到 trace | 确认 Docker 容器正在运行，OTLP endpoint 配置正确（注意端口映射） |
| 连接错误 | 检查网络连通性，确认 14317 端口可访问（或您映射的其他端口） |
| 指标缺失 | 确认 `enable_metrics=True` 已在 `PipelineParams` 中设置 |
| 调试验证 | 设置 `OTEL_CONSOLE_EXPORT=true`，在控制台直接查看 trace 输出 |

### 详细排查步骤

#### 问题 1：Jaeger 中没有显示追踪

**解决方案：**
- 确认 Docker 容器正在运行：`docker ps`
- 检查 OTLP 端点配置是否正确（根据您的端口映射，应为 `http://localhost:14317`）
- 验证 `ENABLE_TRACING=true` 已设置

#### 问题 2：连接错误

**解决方案：**
- 检查网络连接到 Jaeger 容器
- 确认端口 14317（或您映射的端口）没有被防火墙阻止
- 使用 `telnet localhost 14317` 或 `curl http://localhost:14317` 测试连通性

#### 问题 3：导出器问题

**解决方案：**
- 尝试使用控制台导出器进行调试：设置 `OTEL_CONSOLE_EXPORT=true`
- 确认只安装了 gRPC 导出器，而不是 HTTP 导出器

## 参考资料

- [Jaeger 官方文档](https://www.jaegertracing.io/docs/latest/)
- [OpenTelemetry Python 文档](https://opentelemetry.io/docs/languages/python/)
- [Pipecat OpenTelemetry API 参考](https://docs.pipecat.ai/api-reference/server/utilities/opentelemetry)
- [Pipecat GitHub 仓库](https://github.com/pipecat-ai/pipecat)
- [Pipecat Examples](https://github.com/pipecat-ai/pipecat-examples)
