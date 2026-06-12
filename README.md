# SpeeKey

> Speech + Key，语音即按键

一个基于 AI 的智能语音处理系统，集成了语音识别、智能文本预测和语音合成三大核心功能，提供简洁优雅的 Web 界面供用户使用。

---

## 目录

- [项目简介](#项目简介)
- [核心功能](#核心功能)
- [技术栈](#技术栈)
- [功能截图](#功能截图)
- [快速开始](#快速开始)
- [安装步骤](#安装步骤)
- [使用方法](#使用方法)
- [API 文档](#api-文档)
- [项目结构](#项目结构)
- [开发说明](#开发说明)
- [常见问题](#常见问题)
- [许可证](#许可证)

---

## 项目简介

SpeeKey 是一个开源的语音交互系统，将先进的语音识别技术、自然语言处理（NLP）和语音合成技术整合到一个统一的平台中。用户可以通过麦克风输入语音，系统将语音实时转换为文本，同时提供上下文相关的文本预测建议，并支持将任意文本合成为自然语音输出。

### 应用场景

- **辅助输入**：为打字不便的用户提供语音输入替代方案
- **内容创作**：通过语音快速生成文本，辅助写作和笔记
- **多模态交互**：语音输入 + 文本预测 + 语音反馈的完整闭环
- **学习工具**：语言学习、发音练习等场景

---

## 核心功能

### 1. 实时语音识别（Speech-to-Text）
- 支持音频文件上传和实时录音
- 使用 Deepgram 高性能语音识别引擎
- 支持中文和多语言识别
- 自动标点和格式化处理
- **降级模式**：未配置 API Key 时自动使用模拟数据

### 2. 智能文本预测（Text Prediction）
- 基于上下文历史生成预测建议
- 支持部分输入时的智能补全
- 使用 OpenAI / DeepSeek LLM 提供预测能力
- 实时建议，点击即可插入

### 3. 语音合成（Text-to-Speech）
- 支持任意文本转换为自然语音
- 使用 ElevenLabs 多语言语音合成引擎
- 提供高质量、自然流畅的语音输出
- **降级模式**：未配置 API Key 时自动使用模拟数据

### 4. API Key 在线配置
- Web 界面直接配置所有 API 密钥
- 自动保存到 `.env` 文件
- 实时显示各服务的配置状态
- 无需手动编辑配置文件

---

## 技术栈

### 后端
| 组件 | 说明 |
|------|------|
| **Python 3.10+** | 核心编程语言 |
| **FastAPI** | 现代化、高性能的 Web 框架 |
| **Uvicorn** | ASGI 服务器 |
| **Pipecat** | 实时对话和语音处理框架 |

### 外部服务
| 服务 | 用途 | 官方网站 |
|------|------|---------|
| **Deepgram** | 语音识别（STT） | https://deepgram.com |
| **OpenAI / DeepSeek** | 智能文本预测 | https://openai.com / https://deepseek.com |
| **ElevenLabs** | 语音合成（TTS） | https://elevenlabs.io |

### 前端
| 组件 | 说明 |
|------|------|
| **HTML5** | 页面结构 |
| **原生 JavaScript** | 交互逻辑 |
| **CSS3** | 样式设计 |
| **WebSocket** | 实时音频传输 |
| **MediaRecorder API** | 浏览器录音功能 |

---

## 快速开始

### 前置要求

- Python 3.10 或更高版本
- `uv` 包管理器（推荐）或 `pip`
- 可用的麦克风设备
- 浏览器需支持 WebSocket 和 MediaRecorder API（推荐 Chrome/Edge/Firefox 最新版）

### 一键安装

```bash
# 1. 克隆项目
git clone <your-repo-url>
cd speekey

# 2. 安装依赖（使用 uv）
uv install

# 或者使用 pip
pip install -r requirements.txt

# 3. 配置环境变量（复制模板并编辑）
cp .env.example .env
# 编辑 .env 文件填入你的 API Key

# 4. 启动服务
python src/app.py

# 5. 在浏览器中打开
# 访问 http://localhost:8001
```

---

## 安装步骤

### 步骤 1：获取 API 密钥

在启动之前，你需要获取以下服务的 API 密钥（至少配置一个也能使用对应功能）：

1. **Deepgram API Key**（语音识别）
   - 访问 [https://console.deepgram.com/signup](https://console.deepgram.com/signup)
   - 注册账号并创建 API Key
   - 免费额度：$200 免费额度

2. **OpenAI / DeepSeek API Key**（智能预测）
   - OpenAI: [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)
   - DeepSeek: [https://platform.deepseek.com/api_keys](https://platform.deepseek.com/api_keys)
   - 任选其一，在 `.env` 中配置对应的 `OPENAI_BASE_URL`

3. **ElevenLabs API Key**（语音合成）
   - 访问 [https://elevenlabs.io/app/settings/api-keys](https://elevenlabs.io/app/settings/api-keys)
   - 注册账号并生成 API Key
   - 免费额度：每月 10,000 字符

### 步骤 2：配置环境变量

#### 方式 A：通过 Web 界面配置（推荐）

无需手动编辑文件，直接启动后通过浏览器配置：

```bash
python src/app.py
# 访问 http://localhost:8001
# 点击右上角的 "API设置" 标签
# 填入你的 API Key 并点击"保存"
```

#### 方式 B：手动编辑 `.env` 文件

```bash
# 从模板创建
cp .env.example .env

# 编辑 .env 文件，填入你的密钥
# 示例：
# DEEPGRAM_API_KEY=sk-xxxxxxxxxxxxxxxxxxxx
# OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxx
# OPENAI_BASE_URL=https://api.deepseek.com
# ELEVENLABS_API_KEY=sk_xxxxxxxxxxxxxxxxxxxx
# ELEVENLABS_VOICE_ID=pNInz6obpgDQGcFmaJgB
```

### 步骤 3：安装依赖

**使用 uv（推荐）：**

```bash
# 如果还没有 uv，先安装
curl -LsSf https://astral.sh/uv/install.sh | sh

# 在项目目录中安装依赖
uv install
```

**使用 pip：**

```bash
pip install -r requirements.txt
```

---

## 使用方法

### 启动服务

```bash
python src/app.py
```

启动成功后，你会看到类似输出：

```
警告: DEEPGRAM_API_KEY 未设置，将使用模拟转录
警告: ELEVENLABS_API_KEY 未设置，将使用模拟语音合成
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8001 (Press CTRL+C to quit)
```

打开浏览器访问 `http://localhost:8001` 即可使用。

### Web 界面使用

#### 主功能页面

| 功能区域 | 使用说明 |
|---------|---------|
| **录音控制** | 点击「开始录音」，允许浏览器访问麦克风 |
| **识别结果** | 停止录音后，语音被识别并显示为文本 |
| **智能预测** | 在输入框输入部分文本，系统会自动给出补全建议 |
| **语音合成** | 输入任意文本并点击「合成语音」按钮 |

#### API 设置页面

- 查看当前各服务的配置状态（已设置/未设置）
- 在对应的输入框中填入 API Key
- 点击「保存 API 密钥」按钮
- 系统自动保存到 `.env` 文件并更新运行时配置

---

## API 文档

### 完整接口列表

#### 1. 主页面
```
GET /
```
返回 Web 前端页面

#### 2. WebSocket 语音处理接口
```
WebSocket /ws
```
用于实时音频数据传输和处理。

**使用流程：**
1. 建立 WebSocket 连接
2. 发送二进制音频数据（WebM/WAV 格式）
3. 接收返回的文本转录结果

**示例（JavaScript）：**
```javascript
const socket = new WebSocket('ws://localhost:8001/ws');
socket.onmessage = (event) => {
    console.log('识别结果:', event.data);
};
// 发送音频数据
socket.send(audioData);
```

#### 3. 智能预测接口
```
POST /predict
Content-Type: application/json

{
    "partial_text": "今天天气"
}
```

**响应示例：**
```json
{
    "suggestions": [
        "今天天气怎么样？",
        "今天天气真不错",
        "今天天气预报"
    ]
}
```

#### 4. 语音合成接口
```
POST /synthesize
Content-Type: application/json

{
    "text": "你好，欢迎使用 SpeeKey"
}
```

**响应示例：**
```json
{
    "success": true
}
```

#### 5. API 密钥状态查询
```
GET /api-keys
```

**响应示例：**
```json
{
    "deepgram_set": true,
    "openai_set": true,
    "elevenlabs_set": false
}
```

#### 6. API 密钥更新
```
POST /api-keys
Content-Type: application/json

{
    "deepgram_api_key": "sk-new-key-1",
    "openai_api_key": "sk-new-key-2",
    "elevenlabs_api_key": "sk-new-key-3"
}
```

**响应示例：**
```json
{
    "success": true,
    "message": "API密钥已更新"
}
```

---

## 项目结构

```
speekey/
├── src/                          # 源代码目录
│   ├── __init__.py               # 包初始化文件
│   ├── app.py                    # FastAPI 应用入口，路由定义
│   ├── pipeline.py               # 核心处理管线类（STT/LLM/TTS）
│   └── ui/                       # 用户界面
│       └── web/                  # Web 前端
│           └── index.html        # 主页面（包含录音、预测、合成功能）
│
├── tests/                        # 测试目录
│   └── test_pipeline.py          # 管线初始化测试
│
├── .env.example                  # 环境变量模板
├── .gitignore                    # Git 忽略规则
├── .python-version               # Python 版本声明
├── LICENSE                       # 许可证文件
├── README.md                     # 项目说明文档（当前文件）
├── requirements.txt              # pip 依赖列表
├── pyproject.toml                # 项目配置和 uv 依赖声明
└── uv.lock                       # 锁定的依赖版本（自动生成）
```

### 核心模块说明

| 文件 | 功能 |
|------|------|
| [`src/app.py`](src/app.py) | 定义所有 HTTP/WebSocket 路由，处理请求 |
| [`src/pipeline.py`](src/pipeline.py) | `SpeeKeyPipeline` 类，封装所有外部 API 调用逻辑 |
| [`src/ui/web/index.html`](src/ui/web/index.html) | 完整的 Web 前端，包含标签页导航 |
| [`.env.example`](.env.example) | 环境变量模板，包含所有可配置项 |

---

## 开发说明

### 本地开发

```bash
# 克隆后进入目录
cd speekey

# 安装依赖
uv install  # 或 pip install -r requirements.txt

# 启动开发服务器（代码变更后手动重启）
python src/app.py
```

### 添加新功能

**扩展语音识别模型：**
编辑 [`src/pipeline.py`](src/pipeline.py) 中的 `run()` 方法，修改 `PrerecordedOptions` 配置：

```python
options = PrerecordedOptions(
    model="nova-3",       # 可更换为其他模型
    language="en",        # 改为其他语言代码
    smart_format=True,
    punctuate=True
)
```

**自定义语音声音：**
在 `.env` 中修改 `ELEVENLABS_VOICE_ID`，或在 [`src/pipeline.py`](src/pipeline.py) 中调整 `text_to_speech.convert()` 参数。

**修改 LLM 模型：**
在 [`src/pipeline.py`](src/pipeline.py) 中找到调用处：
```python
model="deepseek-ai/DeepSeek-V3.2"  # 改为你的目标模型名称
```

### 代码规范

项目遵循 Python 代码规范，建议使用以下工具进行代码检查：

```bash
# 安装开发依赖
pip install black flake8 pytest

# 代码格式化
black src/

# 静态检查
flake8 src/

# 运行测试
pytest tests/
```

---

## 常见问题

### Q1: 启动时提示 "DEEPGRAM_API_KEY 未设置" 怎么办？
**A:** 这是正常的降级模式。你可以：
- 通过 Web 界面的「API设置」填入 API Key 并保存
- 或手动编辑 `.env` 文件添加 `DEEPGRAM_API_KEY=你的密钥`

### Q2: 浏览器无法录音怎么办？
**A:** 请检查：
1. 浏览器是否允许麦克风权限（首次使用会弹出授权请求）
2. 操作系统的麦克风隐私设置是否允许浏览器访问
3. 麦克风设备是否正常工作
4. 访问地址是否为 `localhost` 或 `https`（非安全域名下部分浏览器禁用麦克风）

### Q3: 如何修改服务端口？
**A:** 编辑 [`src/app.py`](src/app.py) 最后一行：
```python
uvicorn.run(app, host="0.0.0.0", port=8001)  # 修改 port 值
```

### Q4: API 调用失败怎么办？
**A:** 检查：
1. API Key 是否正确（不要有多余空格）
2. 账户余额是否充足
3. 网络是否通畅（部分服务商可能需要代理）
4. 查看控制台输出的详细错误信息

### Q5: 支持哪些音频格式？
**A:** Web 端默认使用 MediaRecorder 生成的 WebM 格式，Deepgram 支持 WAV、MP3、WebM、M4A 等常见格式。

### Q6: 如何在局域网/公网访问？
**A:** 服务默认监听 `0.0.0.0:8001`，局域网内其他设备可通过 `http://<你的IP>:8001` 访问。注意：非 `localhost` 访问时，浏览器要求 HTTPS 才能使用麦克风。

### Q7: 中文语音识别效果如何？
**A:** Deepgram 的 `nova-3` 模型对中文支持良好，搭配 `language="zh"` 参数可获得较好的识别效果。

---

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件。

---

## 致谢

- [Deepgram](https://deepgram.com) - 高性能语音识别
- [ElevenLabs](https://elevenlabs.io) - 自然语音合成
- [FastAPI](https://fastapi.tiangolo.com) - 现代化 Python Web 框架
- [Pipecat](https://pipecat.ai) - 实时对话框架

---

## 联系方式

如有问题或建议，欢迎提交 Issue。

---

**SpeeKey** - 让语音输入像按键一样简单自然 🎤
