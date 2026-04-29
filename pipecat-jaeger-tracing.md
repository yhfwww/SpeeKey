# Pipecat Jaeger 追踪文档

本指南展示了如何在 Pipecat 服务中集成 OpenTelemetry 追踪功能，使用 Jaeger 来可视化服务调用、性能指标和依赖关系。

## 目录

- [概述](#概述)
- [快速开始](#快速开始)
- [配置详解](#配置详解)
- [代码示例](#代码示例)
- [故障排除](#故障排除)
- [参考资料](#参考资料)

## 概述

Pipecat 通过 OpenTelemetry 提供了完整的分布式追踪功能，让你能够：

- 可视化服务调用链
- 监控性能指标
- 追踪依赖关系
- 诊断性能瓶颈

## 快速开始

### 1. 启动 Jaeger 容器

使用 Docker 运行 Jaeger 来收集和可视化追踪数据：

```bash
docker run -d --name jaeger \
  -e COLLECTOR_ZIPKIN_HOST_PORT=:9411 \
  -p 16686:16686 \
  -p 4317:4317 \
  -p 4318:4318 \
  jaegertracing/all-in-one:latest
```

**端口说明：**
- `16686`: Jaeger UI 界面
- `4317`: OTLP gRPC 接收端
- `4318`: OTLP HTTP 接收端

### 2. 配置环境变量

创建 `.env` 文件，配置你的 API 密钥并启用追踪：

```env
# 服务 API 密钥
DEEPGRAM_API_KEY=your_key_here
CARTESIA_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here

# 启用追踪
ENABLE_TRACING=true

# OTLP 端点（默认指向本地 Jaeger）
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317

# 启用控制台输出用于调试（可选）
# OTEL_CONSOLE_EXPORT=true
```

### 3. 安装依赖

使用 uv 安装项目依赖：

```bash
uv sync
```

> **注意**：确保只安装 grpc 导出器。如果存在冲突，请卸载 http 导出器。

### 4. 运行示例

```bash
uv run bot.py
```

### 5. 在 Jaeger 中查看追踪

打开浏览器访问 [http://localhost:16686](http://localhost:16686)，选择 "pipecat-demo" 服务来查看追踪数据。

## 配置详解

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `ENABLE_TRACING` | 是否启用追踪 | - |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | OTLP 导出器端点 | `http://localhost:4317` |
| `OTEL_CONSOLE_EXPORT` | 是否启用控制台输出用于调试 | - |

### 依赖配置

在 `pyproject.toml` 中定义了项目依赖：

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

# 初始化追踪（如果启用）
if IS_TRACING_ENABLED:
    # 创建导出器
    otlp_exporter = OTLPSpanExporter(
        endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317"),
        insecure=True,
    )
    
    # 设置追踪
    setup_tracing(
        service_name="pipecat-demo",
        exporter=otlp_exporter,
        console_export=bool(os.getenv("OTEL_CONSOLE_EXPORT")),
    )
    
    logger.info("OpenTelemetry tracing initialized")

async def fetch_weather_from_api(params: FunctionCallParams):
    await params.result_callback({"conditions": "nice", "temperature": "75"})

# 我们存储函数，这样对象（如 SileroVADAnalyzer）不会被实例化
# 当选择所需的传输时，函数将被调用
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
            system_instruction="You are a helpful LLM in a WebRTC call. Your goal is to demonstrate your capabilities in a succinct way. Your output will be converted to audio so don't include special characters in your answers. Respond to what the user said in a creative and helpful way.",
        ),
    )
    
    # 你也可以注册一个函数名 None 来获取所有函数
    # 发送到同一个回调，并带有额外的 function_name 参数
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
                "description": "The temperature unit to use. Infer this from the user's location.",
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
    
    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            enable_metrics=True,
            enable_usage_metrics=True,
        ),
        enable_tracing=IS_TRACING_ENABLED,
        # 可选：添加对话 ID 来跟踪对话
        # conversation_id="8df26cc1-6db0-4a7a-9930-1e037c8f1fa2",
    )
    
    @transport.event_handler("on_client_connected")
    async def on_client_connected(transport, client):
        logger.info(f"Client connected")
        # 开始对话
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
        enable_metrics=True,
        enable_usage_metrics=True,
    ),
    enable_tracing=IS_TRACING_ENABLED,
    # 可选：添加对话 ID
    # conversation_id="8df26cc1-6db0-4a7a-9930-1e037c8f1fa2",
)
```

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

### 问题 1：Jaeger 中没有显示追踪

**解决方案：**
- 确认 Docker 容器正在运行：`docker ps`
- 检查 OTLP 端点配置是否正确
- 验证 `ENABLE_TRACING=true` 已设置

### 问题 2：连接错误

**解决方案：**
- 检查网络连接到 Jaeger 容器
- 确认端口 4317 没有被防火墙阻止

### 问题 3：导出器问题

**解决方案：**
- 尝试使用控制台导出器进行调试：设置 `OTEL_CONSOLE_EXPORT=true`
- 确认只安装了 gRPC 导出器，而不是 HTTP 导出器

## 参考资料

- [Jaeger 官方文档](https://www.jaegertracing.io/docs/latest/)
- [OpenTelemetry Python 文档](https://opentelemetry.io/docs/languages/python/)
- [Pipecat GitHub 仓库](https://github.com/pipecat-ai/pipecat)
- [Pipecat Examples](https://github.com/pipecat-ai/pipecat-examples)
