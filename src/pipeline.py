from dotenv import load_dotenv
import os
import asyncio
import openai
from deepgram import DeepgramClient, PrerecordedOptions, FileSource
from elevenlabs.client import ElevenLabs
from io import BytesIO

# 加载环境变量
load_dotenv()

class SpeeKeyPipeline:
    def __init__(self):
        # 初始化OpenAI客户端
        self.openai_client = openai.OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL")
        )
        
        # 初始化Deepgram客户端
        self.deepgram_api_key = os.getenv("DEEPGRAM_API_KEY")
        if self.deepgram_api_key:
            self.deepgram_client = DeepgramClient(self.deepgram_api_key)
        else:
            self.deepgram_client = None
            print("警告: DEEPGRAM_API_KEY 未设置，将使用模拟转录")
        
        # 初始化ElevenLabs客户端
        self.elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
        self.elevenlabs_voice_id = os.getenv("ELEVENLABS_VOICE_ID", "pNInz6obpgDQGcFmaJgB")
        if self.elevenlabs_api_key:
            self.elevenlabs_client = ElevenLabs(api_key=self.elevenlabs_api_key)
        else:
            self.elevenlabs_client = None
            print("警告: ELEVENLABS_API_KEY 未设置，将使用模拟语音合成")
        
        # 上下文管理
        self.context = []
    
    async def run(self, audio_data):
        # 调用Deepgram API进行语音识别
        if self.deepgram_client and self.deepgram_api_key:
            try:
                # 准备音频数据
                audio_source = FileSource(buffer=BytesIO(audio_data))
                
                # 配置转录选项
                options = PrerecordedOptions(
                    model="nova-3",
                    language="zh",
                    smart_format=True,
                    punctuate=True
                )
                
                # 调用Deepgram API
                response = self.deepgram_client.listen.prerecorded.v("1").transcribe_file(
                    audio_source, options
                )
                
                # 提取转录结果
                transcription = ""
                if response.results.channels:
                    for channel in response.results.channels:
                        for alternative in channel.alternatives:
                            transcription += alternative.transcript
                
                # 如果没有结果，使用模拟数据
                if not transcription:
                    transcription = "你好，这是一个测试"
                    
            except Exception as e:
                print(f"Deepgram转录错误: {e}")
                transcription = "你好，这是一个测试"
        else:
            transcription = "你好，这是一个测试"
        
        # 添加到上下文
        if transcription:
            self.context.append({"role": "user", "content": transcription})
            # 限制上下文长度
            if len(self.context) > 10:
                self.context = self.context[-10:]
        
        return transcription
    
    async def get_prediction(self, partial_text):
        # 基于部分文本生成预测建议
        if not partial_text:
            return []
        
        # 构建提示
        prompt = "基于以下上下文和部分输入，生成3个可能的完整输入建议：\n\n"
        
        # 添加上下文
        for item in self.context:
            prompt += f"{item['role']}: {item['content']}\n"
        
        prompt += f"\n部分输入: {partial_text}\n\n建议:"
        
        # 调用OpenAI API
        try:
            response = self.openai_client.chat.completions.create(
                model="deepseek-ai/DeepSeek-V3.2",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=100
            )
            
            response_text = response.choices[0].message.content
            
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
        # 将文本合成为语音
        if not text:
            return None
        
        if self.elevenlabs_client and self.elevenlabs_api_key:
            try:
                # 调用ElevenLabs API
                audio_generator = self.elevenlabs_client.text_to_speech.convert(
                    voice_id=self.elevenlabs_voice_id,
                    text=text,
                    model_id="eleven_multilingual_v2",
                    output_format="mp3_44100_128"
                )
                
                # 将生成器转换为字节
                audio_data = b""
                for chunk in audio_generator:
                    audio_data += chunk
                
                return audio_data
            except Exception as e:
                print(f"ElevenLabs语音合成错误: {e}")
                # 如果失败，返回模拟数据
                return b"mock audio data"
        else:
            # 返回模拟音频数据
            return b"mock audio data"
    
    def update_api_keys(self, deepgram_key=None, openai_key=None, elevenlabs_key=None):
        # 更新API密钥
        if deepgram_key is not None:
            self.deepgram_api_key = deepgram_key
            if deepgram_key:
                self.deepgram_client = DeepgramClient(deepgram_key)
            else:
                self.deepgram_client = None
        
        if openai_key is not None:
            self.openai_client = openai.OpenAI(
                api_key=openai_key,
                base_url=os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com")
            )
        
        if elevenlabs_key is not None:
            self.elevenlabs_api_key = elevenlabs_key
            if elevenlabs_key:
                self.elevenlabs_client = ElevenLabs(api_key=elevenlabs_key)
            else:
                self.elevenlabs_client = None
