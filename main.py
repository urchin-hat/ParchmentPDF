from fastapi import FastAPI, Request, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

app = FastAPI(title="ParchmentPDF")

# Static files and Templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse(
        request=request, name="index.html", context={}
    )

@app.post("/convert")
async def convert_pdf(request: Request, file: UploadFile = File(...)):
    # TODO: Implement PDF conversion logic
    # 暫定的にファイル名を表示するレスポンスを返す
    return HTMLResponse(content=f"<div class='p-4 bg-green-100 text-green-700 rounded-lg'>Received: {file.filename}</div>")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
