from pipecat.pipeline.pipeline import Pipeline
from pipecat.services.deepgram.stt import DeepgramSTTService
from pipecat.services.openai.llm import OpenAILLMService
from pipecat.services.elevenlabs.tts import ElevenLabsTTSService
from pipecat.transcriptions.language import Language
from pipecat.frames.frames import OutputAudioRawFrame, TextFrame, TranscriptionFrame
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()

class SpeeKeyPipeline:
    def __init__(self):
        # 初始化服务
        self.stt = DeepgramSTTService(
            api_key=os.getenv("DEEPGRAM_API_KEY"),
            language=Language.ZH_CN
        )
        
        self.llm = OpenAILLMService(
            api_key=os.getenv("OPENAI_API_KEY"),
            settings=OpenAILLMService.Settings(model="gpt-4")
        )
        
        self.tts = ElevenLabsTTSService(
            api_key=os.getenv("ELEVENLABS_API_KEY")
        )
        
        # 创建管线
        self.pipeline = Pipeline([
            self.stt,
            self.llm,
            self.tts
        ])
        
        # 上下文管理
        self.context = []
    
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
