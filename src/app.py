from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

app = FastAPI()

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 延迟初始化管线
pipeline = None

async def get_pipeline():
    global pipeline
    if pipeline is None:
        from pipeline import SpeeKeyPipeline
        pipeline = SpeeKeyPipeline()
    return pipeline

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
            pipeline = await get_pipeline()
            result = await pipeline.run(data)
            # 返回识别结果
            await websocket.send_text(result)
    except Exception as e:
        print(f"WebSocket error: {e}")
        await websocket.send_text(f"Error: {str(e)}")
    finally:
        await websocket.close()

from pydantic import BaseModel

class PredictionRequest(BaseModel):
    partial_text: str

@app.post("/predict")
async def get_prediction(request: PredictionRequest):
    """获取输入预测建议"""
    try:
        pipeline = await get_pipeline()
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
        pipeline = await get_pipeline()
        audio_data = await pipeline.synthesize_speech(request.text)
        if audio_data:
            return {"success": True}
        else:
            return {"success": False, "message": "语音合成失败"}
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
