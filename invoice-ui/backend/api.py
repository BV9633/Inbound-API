import os
import json
import logging
import asyncio
from typing import List, AsyncGenerator
from datetime import datetime

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

from extraction_service import extract_invoice_from_bytes_with_status

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Constants
VALID_EXTENSIONS = [".xlsx", ".xls"]

# Create FastAPI application
app = FastAPI(
    title="Invoice Extraction API",
    description="Extract structured data from supplier invoices with real-time status",
    version="1.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Invoice Extraction API"
    }


@app.post("/extract")
async def extract_single_file(file: UploadFile = File(...)):
    """
    Extract invoice data from a single Excel file.
    Returns JSON with extraction results.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in VALID_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Invalid file type. Allowed: {VALID_EXTENSIONS}")
    
    try:
        logger.info(f"Processing file: {file.filename}")
        file_bytes = await file.read()
        
        if len(file_bytes) == 0:
            raise HTTPException(status_code=400, detail="Empty file uploaded")
        
        # Use the standard extraction (without streaming)
        from extraction_service import extract_invoice_from_bytes
        result = extract_invoice_from_bytes(file_bytes, file.filename)
        
        return JSONResponse(content=result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Extraction failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")


@app.post("/extract-stream")
async def extract_with_stream(file: UploadFile = File(...)):
    """
    Extract invoice data with streaming status updates.
    
    Returns Server-Sent Events (SSE) with status updates during processing,
    followed by the final result.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in VALID_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Invalid file type. Allowed: {VALID_EXTENSIONS}")
    
    try:
        file_bytes = await file.read()
        
        if len(file_bytes) == 0:
            raise HTTPException(status_code=400, detail="Empty file uploaded")
        
        async def generate_status() -> AsyncGenerator[str, None]:
            """Generate SSE events with status updates."""
            try:
                async for status in extract_invoice_from_bytes_with_status(file_bytes, file.filename):
                    yield f"data: {json.dumps(status)}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        
        return StreamingResponse(
            generate_status(),
            media_type="text/event-stream"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Stream extraction failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")


@app.post("/batch-extract")
async def extract_multiple_files(files: List[UploadFile] = File(...)):
    """Extract invoice data from multiple Excel files."""
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    from extraction_service import extract_invoice_from_bytes
    
    results = {}
    errors = []
    
    for file in files:
        if not file.filename:
            continue
        
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in VALID_EXTENSIONS:
            errors.append({"filename": file.filename, "error": "Invalid file type"})
            continue
        
        try:
            logger.info(f"Processing batch file: {file.filename}")
            file_bytes = await file.read()
            
            if len(file_bytes) == 0:
                errors.append({"filename": file.filename, "error": "Empty file"})
                continue
            
            result = extract_invoice_from_bytes(file_bytes, file.filename)
            results[file.filename] = result
            
        except Exception as e:
            logger.error(f"Failed to process {file.filename}: {e}")
            errors.append({"filename": file.filename, "error": str(e)})
    
    return JSONResponse(content={
        "extracted": results,
        "errors": errors,
        "summary": {
            "total_files": len(files),
            "successful": len(results),
            "failed": len(errors),
            "processed_at": datetime.now().isoformat()
        }
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
