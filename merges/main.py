"""Main file integrating waybill and cbp"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from waybill import waybill_main
from cbp import cbp_main

load_dotenv()

app=FastAPI()


app.include_router(waybill_main.waybill_router)
app.include_router(cbp_main.cbp_router)

CORS_ORIGINS = os.getenv("CORS_ORIGIN")

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