import logging
import os
import tempfile
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from i2pdf import TMP_ROOT, extract_pdf_summary

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("i2pdf-service")

app = FastAPI(
    title="i2pdf Extraction Service",
    description="Service for extracting structured text from PDF files with OCR fallback.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs(TMP_ROOT, exist_ok=True)
logger.info("Using temporary directory %s", TMP_ROOT)


@app.get("/")
async def root():
    return {
        "service": "i2pdf Extraction API",
        "version": "1.0.0",
        "endpoints": {
            "extract": "POST /extract",
            "health": "GET /health",
            "stats": "GET /stats",
        },
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "temp_dir": TMP_ROOT,
        "temp_dir_exists": os.path.exists(TMP_ROOT),
        "temp_dir_writable": os.access(TMP_ROOT, os.W_OK),
    }


@app.post("/extract")
async def extract_pdf(
    file: UploadFile = File(..., description="PDF file"),
    url: str = Form("", description="Original file URL (optional)"),
    language: str = Form("ara", description="Primary OCR language"),
    force_ocr: bool = Form(False, description="Force OCR even if text layer exists"),
) -> JSONResponse:
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF.")

    tmp_path: Optional[str] = None
    try:
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".pdf",
            dir=TMP_ROOT,
            prefix="upload_",
        ) as tmp:
            # reading entire file; adjust if extremely large
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        logger.info("Stored uploaded file %s at %s", file.filename, tmp_path)

        data = extract_pdf_summary(
            pdf_path=tmp_path,
            url=url or file.filename,
            lang=language,
            force_ocr=force_ocr,
        )

        return JSONResponse(content=data, status_code=200)
    except ValueError as exc:
        logger.warning("Bad request when processing %s: %s", file.filename, exc)
        raise HTTPException(status_code=400, detail=str(exc))
    except FileNotFoundError as exc:
        logger.error("Temporary file vanished: %s", exc)
        raise HTTPException(status_code=500, detail="Temporary file not found.")
    except Exception as exc:
        logger.exception("Extraction failed for %s", file.filename)
        raise HTTPException(status_code=500, detail=f"Extraction failed: {exc}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
                logger.debug("Removed temporary file %s", tmp_path)
            except Exception as cleanup_exc:
                logger.warning("Failed to remove temporary file %s: %s", tmp_path, cleanup_exc)


@app.get("/stats")
async def stats():
    try:
        files = list(Path(TMP_ROOT).glob("*"))
        total_size = sum(f.stat().st_size for f in files if f.is_file())
        return {
            "temp_dir": TMP_ROOT,
            "file_count": len([f for f in files if f.is_file()]),
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "files": [
                {
                    "name": f.name,
                    "size_kb": round(f.stat().st_size / 1024, 2),
                    "modified": f.stat().st_mtime,
                }
                for f in sorted(files, key=lambda x: x.stat().st_mtime, reverse=True)
                if f.is_file()
            ][:10],
        }
    except Exception as exc:
        logger.exception("Failed to read stats")
        return {"error": str(exc), "temp_dir": TMP_ROOT}


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8080"))
    host = os.getenv("HOST", "0.0.0.0")
    logger.info("Starting i2pdf service on %s:%s", host, port)
    uvicorn.run("service:app", host=host, port=port, log_level="info")

