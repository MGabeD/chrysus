import os
import shutil
import asyncio
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from pathlib import Path

from chrysus.backend.core.accounts_controller import AccountsController
from chrysus.utils.logger import get_logger
from chrysus import resolve_component_dirs_path
from fastapi.middleware.cors import CORSMiddleware

logger = get_logger(__name__)

app = FastAPI()
accounts_controller = AccountsController()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/upload_pdf/")
async def upload_pdf(file: UploadFile = File(...)):
    filename = os.path.basename(file.filename)
    data_dir = resolve_component_dirs_path("data")
    save_path = data_dir / filename
    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    try:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,  
            accounts_controller.extract_tables_from_pdf_and_add_to_self,
            save_path,
        )
        logger.info(f"Extracted tables from {filename}")
        logger.info(f"Account holder map: {accounts_controller.account_holder_map}")
    except Exception as e:
        logger.error(f"Extraction error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    return {"success": True}

# @app.post("/upload_pdf/")
# async def upload_pdf(file: UploadFile = File(...)):
#     filename = os.path.basename(file.filename)
#     data_dir = resolve_component_dirs_path("data")
#     save_path = data_dir / filename
#     with open(save_path, "wb") as buffer:
#         shutil.copyfileobj(file.file, buffer)
#     try:
#         accounts_controller.extract_tables_from_pdf_and_add_to_self(save_path)
#         logger.info(f"Extracted tables from {filename}")
#         logger.info(f"Account holder map: {accounts_controller.account_holder_map}")
#     except Exception as e:
#         raise HTTPException(status_code=400, detail=str(e))
#     return {"success": True}

@app.get("/users")
def get_users():
    logger.info(f"Account holder map: {accounts_controller.account_holder_map}")
    res_packet = {"users": list(accounts_controller.account_holder_map.keys())}
    logger.info(f"Users packet: {res_packet}")
    return res_packet

@app.get("/user/{name}/base_insights")
def get_base_insights(name: str):
    holder = accounts_controller.get_account_holder(name)
    if not holder:
        raise HTTPException(status_code=404, detail="Account holder not found")
    packet = holder.get_base_insights()
    logger.info(f"Base insights: {packet}")
    return packet

@app.get("/user/{name}/transaction_table")
def get_transaction_table(name: str):
    holder = accounts_controller.get_account_holder(name)
    if not holder:
        raise HTTPException(status_code=404, detail="Account holder not found")
    
    transaction_table = holder.get_transaction_table_json()
    if transaction_table is None:
        raise HTTPException(status_code=404, detail="No transaction table found for this user")
    
    return transaction_table

@app.get("/user/{name}/descriptive_tables")
def get_descriptive_tables(name: str):
    holder = accounts_controller.get_account_holder(name)
    if not holder:
        raise HTTPException(status_code=404, detail="Account holder not found")
    
    descriptive_tables = holder.get_descriptive_tables_json()
    logger.info(f"Descriptive tables: {descriptive_tables}")
    return descriptive_tables

@app.get("/user/{name}/recommendations")
def get_recommendations(name: str):
    holder = accounts_controller.get_account_holder(name)
    if not holder:
        raise HTTPException(status_code=404, detail="Account holder not found")
    
    recommendations = holder.get_recommendations()
    if "error" in recommendations:
        raise HTTPException(status_code=500, detail=recommendations["error"])
    logger.info(f"Recommendations: {recommendations}")
    return recommendations

