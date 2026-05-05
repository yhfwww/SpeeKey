from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
import uvicorn
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from pipeline import SpeeKeyPipeline
from pydantic import BaseModel

app = FastAPI()

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化管线
pipeline = SpeeKeyPipeline()

# API密钥配置模型
class APIKeysRequest(BaseModel):
    deepgram_api_key: str = ""
    openai_api_key: str = ""
    elevenlabs_api_key: str = ""

@app.get("/")
async def read_root():
    # 返回前端页面
    html_path = os.path.join(os.path.dirname(__file__), "ui", "web", "index.html")
    if os.path.exists(html_path):
        return FileResponse(html_path)
    return {"message": "SpeeKey API is running"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_bytes()
            # 处理音频数据
            result = await pipeline.run(data)
            # 返回识别结果
            await websocket.send_text(result)
    except Exception as e:
        print(f"WebSocket error: {e}")
        await websocket.send_text(f"Error: {str(e)}")
    finally:
        await websocket.close()

class PredictionRequest(BaseModel):
    partial_text: str

@app.post("/predict")
async def get_prediction(request: PredictionRequest):
    """获取输入预测建议"""
    try:
        suggestions = await pipeline.get_prediction(request.partial_text)
        return {"suggestions": suggestions}
    except Exception as e:
        return {"error": str(e)}

class SynthesisRequest(BaseModel):
    text: str

@app.post("/synthesize")
async def synthesize_speech(request: SynthesisRequest):
    """将文本合成为语音"""
    try:
        audio_data = await pipeline.synthesize_speech(request.text)
        if audio_data:
            return {"success": True}
        else:
            return {"success": False, "message": "语音合成失败"}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api-keys")
async def get_api_keys_status():
    """获取当前API密钥状态（是否已设置）"""
    return {
        "deepgram_set": pipeline.deepgram_api_key is not None and pipeline.deepgram_api_key != "",
        "openai_set": os.getenv("OPENAI_API_KEY") is not None and os.getenv("OPENAI_API_KEY") != "",
        "elevenlabs_set": pipeline.elevenlabs_api_key is not None and pipeline.elevenlabs_api_key != ""
    }

@app.post("/api-keys")
async def update_api_keys(request: APIKeysRequest):
    """更新API密钥"""
    try:
        pipeline.update_api_keys(
            deepgram_key=request.deepgram_api_key,
            openai_key=request.openai_api_key,
            elevenlabs_key=request.elevenlabs_api_key
        )
        
        # 保存到.env文件
        env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
        
        # 读取现有.env文件
        env_content = []
        if os.path.exists(env_path):
            with open(env_path, 'r', encoding='utf-8') as f:
                env_content = f.readlines()
        
        # 更新或添加API密钥
        keys_to_update = {
            "DEEPGRAM_API_KEY": request.deepgram_api_key,
            "OPENAI_API_KEY": request.openai_api_key,
            "ELEVENLABS_API_KEY": request.elevenlabs_api_key
        }
        
        for key, value in keys_to_update.items():
            found = False
            for i, line in enumerate(env_content):
                if line.strip().startswith(key + "="):
                    env_content[i] = f"{key}={value}\n"
                    found = True
                    break
            if not found:
                env_content.append(f"{key}={value}\n")
        
        # 写入.env文件
        with open(env_path, 'w', encoding='utf-8') as f:
            f.writelines(env_content)
        
        return {"success": True, "message": "API密钥已更新"}
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
