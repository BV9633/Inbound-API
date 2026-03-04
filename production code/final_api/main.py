"""Main file integrating waybill and cbp"""
import os
from parameterManager import get_parameter_labels
import google.auth
import logging
from google.cloud.logging.handlers import StructuredLogHandler

# Setup Logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.handlers.clear()
handler = StructuredLogHandler()
logger.addHandler(handler)



_, project_id = google.auth.default()
if not project_id:
    raise RuntimeError("Project ID not fetched/found. Cloud run should always provide it.")
os.environ["PROJECT_ID"] = project_id

try:
    labels = get_parameter_labels(
        project_id= os.getenv("PROJECT_ID"),
        location="global",
        parameter_id="DARK_DATA_TRANSFORMATION"
    )
    for key in labels:
        os.environ[key] = labels.get(key)
    #  print("fetched from env for parameters========>",os.getenv(key))
except Exception as e:
    logger.error("exception: %s", e)



from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from waybill import waybill_main
from cbp import cbp_main
from invoice import invoice_main
from dashboard import dashboard_main,dashboard2
from users import user_main
from exceptional import exceptional_main


load_dotenv()

app=FastAPI(title="DDT API's")


app.include_router(waybill_main.waybill_router)
app.include_router(cbp_main.cbp_router)
app.include_router(invoice_main.invoice_router)
app.include_router(dashboard_main.dashboard_router)
app.include_router(dashboard2.dashboard_router)
app.include_router(user_main.user_router)
app.include_router(exceptional_main.exceptions_router)

CORS_ORIGINS = os.getenv("DDT_CORS_ORIGIN")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],        
    allow_headers=["*"],        
)

@app.get("/")
def Home():
    return "working"