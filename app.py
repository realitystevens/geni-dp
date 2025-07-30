import io
import uvicorn
from PIL import Image
from fastapi import Request
from fastapi import FastAPI, File, UploadFile
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, StreamingResponse


app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/generate")
async def generate_image(file: UploadFile = File(...)):
    user_image = Image.open(file.file).convert("RGBA")
    background = Image.open("static/assets/generation_intimacy.png").convert("RGBA")

    # Resize user image (optional logic)
    user_image = user_image.resize((400, 400))  # change size as needed

    # Paste user image onto background
    # coordinates + transparency
    background.paste(user_image, (200, 500), user_image)

    # Save to a BytesIO buffer
    buffer = io.BytesIO()
    background.save(buffer, format="PNG")
    buffer.seek(0)

    return StreamingResponse(buffer, media_type="image/png")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
