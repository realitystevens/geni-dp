import io
import json
import uvicorn
from PIL import Image
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from utils import is_image_transparent, remove_background, crop_and_resize_with_outline


app = FastAPI(
    docs_url=None,
    redoc_url=None,
    openapi_url=None
)
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.websocket("/generate")
async def generate_image(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_bytes()
            """
            Client sends the user image as bytes (PNG/JPEG)
            """
            background = Image.open("static/assets/generation_intimacy.png").convert("RGBA")
            user_image = Image.open(io.BytesIO(data)).convert("RGBA")
            
            # Check if user_image is fully transparent
            if not is_image_transparent(user_image):
                try:
                    result = remove_background(user_image)
                except Exception as e:
                    error_message = {"error": f"Background removal failed: {str(e)}"}
                    print(error_message)
                    await websocket.send_text(json.dumps(error_message))
                    continue
                user_image = result

            # Crop, resize, and add outline
            try:
                user_image = crop_and_resize_with_outline(user_image, target_width=800)
            except Exception as e:
                error_message = {"error": f"Image processing failed: {str(e)}"}
                await websocket.send_text(json.dumps(error_message))
                continue

            # Calculate position to paste user image
            x = (background.width - user_image.width) // 2
            y = background.height - user_image.height + 300

            # Paste user image onto background
            background.paste(user_image, (x, y), user_image)

            # Save to a BytesIO buffer
            buffer = io.BytesIO()
            background.save(buffer, format="PNG")
            buffer.seek(0)

            # Send the resulting image back as bytes
            await websocket.send_bytes(buffer.getvalue())
    except WebSocketDisconnect:
        print("WebSocket disconnected")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
