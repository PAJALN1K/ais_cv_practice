import uuid
import cv2 as cv
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Request, Form
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.detector import MotoDetector
from src.data_manager import DataManager

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent
SRC_DIR = BASE_DIR / "src"
DATA_DIR = BASE_DIR / "data"

dm = DataManager()
detector = MotoDetector()

templates = Jinja2Templates(directory=str(SRC_DIR / "templates"))

app.mount("/data", StaticFiles(directory=str(DATA_DIR)), name="data")

DEFAULT_LANE = [[0.4, 0.7], [0.6, 0.7], [0.9, 1.0], [0.1, 1.0]]


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    result = request.query_params.get("result")
    m = request.query_params.get("m", 0)
    v = request.query_params.get("v", 0)

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "history": dm.load_history(),
            "result": result,
            "m": m,
            "v": v,
        },
    )


@app.post("/upload")
async def process(file: UploadFile = File(...), coords: str = Form(None)):
    suffix = Path(file.filename).suffix
    unique_name = f"{uuid.uuid4()}{suffix}"
    input_path = dm.inputs_dir / unique_name

    with open(input_path, "wb") as f:
        f.write(await file.read())

    lane_polygon = DEFAULT_LANE
    if coords:
        try:
            pairs = [p.strip() for p in coords.split(";") if p.strip()]
            custom_poly = [[float(c) for c in p.split(",")] for p in pairs]
            if len(custom_poly) >= 3:
                lane_polygon = custom_poly
        except:
            pass

    img = cv.imread(str(input_path))
    res_img, m_count, v_count = detector.process_frame(img, lane_polygon)

    result_filename = f"res_{unique_name}"
    result_path = dm.results_dir / result_filename
    cv.imwrite(str(result_path), res_img)

    dm.save_record(file.filename, m_count, v_count)

    return RedirectResponse(
        url=f"/?result=results/{result_filename}&m={m_count}&v={v_count}",
        status_code=303,
    )


@app.get("/download-report")
async def download_report():
    try:
        path = dm.generate_pdf()
        return FileResponse(
            path,
            media_type="application/pdf",
            filename=f"report_{uuid.uuid4().hex[:8]}.pdf",
        )
    except Exception as e:
        return {"error": f"Ошибка генерации отчета: {str(e)}"}


@app.get("/download-excel")
async def download_excel():
    try:
        path = dm.generate_xlsx()
        if not path:
            return {"error": "История пуста, нечего экспортировать"}

        return FileResponse(
            path,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=f"traffic_report_{uuid.uuid4().hex[:8]}.xlsx",
        )
    except Exception as e:
        return {"error": f"Ошибка генерации Excel: {str(e)}"}


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)
