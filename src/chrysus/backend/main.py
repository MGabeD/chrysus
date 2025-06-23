import os
import shutil
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from pathlib import Path

from chrysus.backend.core.accounts_controller import AccountsController
from chrysus import resolve_component_dirs_path

app = FastAPI()
accounts_controller = AccountsController()

@app.post("/upload_pdf/")
async def upload_pdf(file: UploadFile = File(...)):
    filename = os.path.basename(file.filename)
    data_dir = resolve_component_dirs_path("data")
    save_path = data_dir / filename
    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    try:
        accounts_controller.extract_tables_from_pdf_and_add_to_self(save_path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"success": True}

@app.get("/users")
def get_users():
    return {"users": list(accounts_controller.account_holder_map.keys())}

@app.get("/user/{name}/base_insights")
def get_base_insights(name: str):
    holder = accounts_controller.get_account_holder(name)
    if not holder:
        raise HTTPException(status_code=404, detail="Account holder not found")
    return holder.get_base_insights()

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
    return descriptive_tables
