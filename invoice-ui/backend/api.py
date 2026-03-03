import os
import json
import logging
from typing import List, AsyncGenerator
from datetime import datetime

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

from extraction_service import extract_invoice_from_bytes, extract_invoice_from_bytes_with_status

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("api")

# Constants
VALID_EXTENSIONS = [".xlsx", ".xls"]

app = FastAPI(
    title="Invoice Extraction API",
    description="Enterprise-grade invoice data extraction from Excel files.",
    version="1.2.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Invoice Extraction API"
    }

@app.post("/extract")
async def extract_single_file(file: UploadFile = File(...)):
    """Extract invoice data from a single Excel file (Synchronous)."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")
    
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in VALID_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Invalid file type. Allowed extensions: {VALID_EXTENSIONS}")
    
    try:
        logger.info(f"Processing invoice file: {file.filename}")
        file_bytes = await file.read()
        
        if len(file_bytes) == 0:
            raise HTTPException(status_code=400, detail="File is empty.")
        
        result = extract_invoice_from_bytes(file_bytes, file.filename)
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"Extraction failed for {file.filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal extraction error: {str(e)}")

@app.post("/extract-stream")
async def extract_with_stream(file: UploadFile = File(...)):
    """Extract invoice data with real-time status updates (SSE)."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")
    
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in VALID_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Invalid file type. Allowed extensions: {VALID_EXTENSIONS}")
    
    try:
        file_bytes = await file.read()
        
        if len(file_bytes) == 0:
            raise HTTPException(status_code=400, detail="File is empty.")
        
        async def generate_status() -> AsyncGenerator[str, None]:
            """Stream processing status as Server-Sent Events."""
            try:
                async for status in extract_invoice_from_bytes_with_status(file_bytes, file.filename):
                    yield f"data: {json.dumps(status)}\n\n"
            except Exception as e:
                logger.error(f"Stream generation error: {e}")
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        
        return StreamingResponse(
            generate_status(),
            media_type="text/event-stream"
        )
        
    except Exception as e:
        logger.error(f"Stream setup failed for {file.filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal stream error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
