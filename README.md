# SpeeKey
Speech+Key，语音即按键

## 项目简介
SpeeKey 是一个语音处理系统，通过集成先进的语音识别、自然语言处理和语音合成技术，实现语音到文本的转换、智能预测建议和文本到语音的合成功能。

## 核心功能
- **实时语音识别**：使用 Deepgram STT 服务将音频转换为文本
- **智能预测建议**：基于上下文和部分输入生成预测建议
- **语音合成**：将文本转换为自然语音
- **WebSocket 接口**：支持实时音频数据传输和处理
- **REST API**：提供预测建议和语音合成的 HTTP 接口

## 技术栈
- **后端**：Python, FastAPI, uvicorn
- **语音服务**：Deepgram STT, OpenAI LLM, ElevenLabs TTS
- **前端**：HTML, JavaScript

## 安装说明
### 使用 uv（推荐）
1. 克隆项目到本地
2. 安装依赖：`uv install`
3. 创建 `.env` 文件并添加以下环境变量：
   - `DEEPGRAM_API_KEY`：Deepgram API 密钥
   - `OPENAI_API_KEY`：OpenAI API 密钥
   - `ELEVENLABS_API_KEY`：ElevenLabs API 密钥

### 使用 pip
1. 克隆项目到本地
2. 安装依赖：`pip install -r requirements.txt`
3. 创建 `.env` 文件并添加以下环境变量：
   - `DEEPGRAM_API_KEY`：Deepgram API 密钥
   - `OPENAI_API_KEY`：OpenAI API 密钥
   - `ELEVENLABS_API_KEY`：ElevenLabs API 密钥

## 使用方法
1. 启动服务：`python src/app.py`
2. 访问 `http://localhost:8000` 打开前端界面
3. 开始使用语音输入和预测功能

## API 接口
- **WebSocket**：`/ws` - 用于实时音频处理
- **POST /predict**：获取输入预测建议
- **POST /synthesize**：将文本合成为语音

## 项目结构
- `src/`：源代码目录
  - `app.py`：FastAPI 应用
  - `pipeline.py`：核心处理管线
  - `ui/web/`：前端界面
- `tests/`：测试目录
- `requirements.txt`：依赖文件
- `.env`：环境变量配置（需自行创建）