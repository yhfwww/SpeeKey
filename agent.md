# SpeeKey Agent 设计与实现

## 1. 核心架构

SpeeKey Agent 是一个基于管线（Pipeline）的语音处理系统，由三个主要服务组成：

- **语音识别服务**（STT）：使用 Deepgram API 将音频转换为文本
- **语言模型服务**（LLM）：使用 OpenAI GPT-4 处理文本和生成预测
- **语音合成服务**（TTS）：使用 ElevenLabs API 将文本转换为语音

## 2. 代理实现

### 2.1 核心类结构

```python
class SpeeKeyPipeline:
    def __init__(self):
        # 初始化服务
        self.stt = DeepgramSTTService(...)
        self.llm = OpenAILLMService(...)
        self.tts = ElevenLabsTTSService(...)
        
        # 创建管线
        self.pipeline = Pipeline([self.stt, self.llm, self.tts])
        
        # 上下文管理
        self.context = []
```

### 2.2 主要方法

#### 2.2.1 音频处理

```python
async def run(self, audio_data):
    # 运行管线处理音频数据
    # 创建音频帧
    audio_frame = OutputAudioRawFrame(audio_data, sample_rate=16000, channels=1)
    
    # 处理结果
    results = []
    
    async for frame in self.pipeline.process(audio_frame):
        if isinstance(frame, (TextFrame, TranscriptionFrame)):
            results.append(frame.text)
    
    transcription = " ".join(results)
    
    # 添加到上下文
    if transcription:
        self.context.append({"role": "user", "content": transcription})
        # 限制上下文长度
        if len(self.context) > 10:
            self.context = self.context[-10:]
    
    return transcription
```

#### 2.2.2 预测建议

```python
async def get_prediction(self, partial_text):
    """基于部分文本生成预测建议"""
    if not partial_text:
        return []
    
    # 构建提示
    prompt = f"基于以下上下文和部分输入，生成3个可能的完整输入建议：\n\n"
    
    # 添加上下文
    for item in self.context:
        prompt += f"{item['role']}: {item['content']}\n"
    
    prompt += f"\n部分输入: {partial_text}\n\n建议:"
    
    # 调用LLM
    try:
        # 创建文本帧
        text_frame = TextFrame(prompt)
        
        # 处理结果
        response_text = ""
        
        async for frame in self.pipeline.process(text_frame):
            if isinstance(frame, (TextFrame, TranscriptionFrame)):
                response_text += frame.text
        
        # 解析响应
        suggestions = []
        if response_text:
            lines = response_text.strip().split('\n')
            for line in lines:
                line = line.strip()
                if line and not line.startswith('建议:'):
                    suggestions.append(line)
        
        return suggestions[:3]
    except Exception as e:
        print(f"预测错误: {e}")
        return []
```

#### 2.2.3 语音合成

```python
async def synthesize_speech(self, text):
    """将文本合成为语音"""
    if not text:
        return None
    
    # 调用TTS服务
    try:
        # 创建文本帧
        text_frame = TextFrame(text)
        
        # 处理结果
        audio_data = None
        
        async for frame in self.pipeline.process(text_frame):
            if hasattr(frame, 'audio'):
                audio_data = frame.audio
                break
        
        return audio_data
    except Exception as e:
        print(f"语音合成错误: {e}")
        return None
```

## 3. 服务集成

### 3.1 Deepgram STT 服务

- **功能**：将音频数据转换为文本
- **配置**：需要 Deepgram API 密钥和语言设置（默认中文）
- **输入**：音频帧（16kHz，单声道）
- **输出**：文本转录结果

### 3.2 OpenAI LLM 服务

- **功能**：处理文本和生成预测建议
- **配置**：需要 OpenAI API 密钥，使用 GPT-4 模型
- **输入**：文本提示（包含上下文和部分输入）
- **输出**：预测建议列表

### 3.3 ElevenLabs TTS 服务

- **功能**：将文本转换为自然语音
- **配置**：需要 ElevenLabs API 密钥
- **输入**：文本
- **输出**：音频数据

## 4. 上下文管理

- **目的**：维护对话历史，提供更准确的预测建议
- **实现**：使用列表存储对话历史，每个条目包含角色和内容
- **限制**：最多保存最近 10 条对话，避免上下文过长

## 5. API 接口

### 5.1 WebSocket 接口

- **路径**：`/ws`
- **功能**：实时音频数据传输和处理
- **流程**：
  1. 客户端建立 WebSocket 连接
  2. 客户端发送音频数据
  3. 服务端处理音频并返回识别结果
  4. 循环处理直到连接关闭

### 5.2 REST API

- **POST /predict**：获取输入预测建议
  - 请求体：`{"partial_text": "部分输入文本"}`
  - 响应：`{"suggestions": ["建议1", "建议2", "建议3"]}`

- **POST /synthesize**：将文本合成为语音
  - 请求体：`{"text": "要合成的文本"}`
  - 响应：`{"success": true}` 或 `{"success": false, "message": "错误信息"}`

## 6. 技术实现细节

- **异步处理**：使用 Python `async`/`await` 实现异步处理，提高并发性能
- **管线模式**：使用 pipecat 库的 Pipeline 模式，实现服务的串联和数据的流式处理
- **环境变量**：使用 dotenv 库加载环境变量，保护 API 密钥
- **错误处理**：实现异常捕获和错误返回，提高系统稳定性

## 7. 扩展与优化

### 7.1 可能的扩展

- **支持多语言**：添加语言选择功能，支持多种语言的语音处理
- **个性化语音**：允许用户选择或训练个性化的语音合成模型
- **离线处理**：集成本地语音处理模型，减少对云服务的依赖
- **用户配置**：添加用户配置界面，允许调整语音识别和合成参数

### 7.2 性能优化

- **缓存机制**：缓存常见的预测建议和语音合成结果
- **批量处理**：优化音频处理流程，支持批量处理
- **资源管理**：合理管理 API 调用频率，避免超出服务限制
- **负载均衡**：在高并发场景下实现负载均衡

## 8. 总结

SpeeKey Agent 是一个集成了先进语音处理技术的智能系统，通过管线架构实现了语音识别、智能预测和语音合成的无缝集成。它提供了实时的 WebSocket 接口和 REST API，方便前端应用和其他系统集成。

该设计具有良好的扩展性和可维护性，可以根据实际需求进行调整和扩展，为用户提供更加智能、高效的语音交互体验。