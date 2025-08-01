import io
import uvicorn
from PIL import Image
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse


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
            
            base_width = 800
            w_percent = base_width / float(user_image.width)
            new_height = int(float(user_image.height) * w_percent)

            user_image = user_image.resize((base_width, new_height), Image.LANCZOS)

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
