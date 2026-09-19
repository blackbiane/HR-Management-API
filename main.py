from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import date

app = FastAPI(
    title="HR API with Batch Operations",
    description="FastAPI example with 3 GET, 3 POST, 3 DELETE, and 3 BATCH endpoints."
)

# ==========================================
# Pydantic Models
# ==========================================
class EmployeeCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    department_id: int

class EmployeeResponse(EmployeeCreate):
    id: int

class DepartmentCreate(BaseModel):
    name: str

class DepartmentResponse(DepartmentCreate):
    id: int

class BatchDeleteRequest(BaseModel):
    employee_ids: List[int]

class BatchStatusUpdate(BaseModel):
    employee_id: int
    is_active: bool

# ==========================================
# Mock Database
# ==========================================
db_employees = [
    {"id": 1, "first_name": "John", "last_name": "Doe", "email": "john@example.com", "department_id": 1, "is_active": True},
    {"id": 2, "first_name": "Jane", "last_name": "Smith", "email": "jane@example.com", "department_id": 1, "is_active": True}
]
db_departments = [
    {"id": 1, "name": "Engineering"},
    {"id": 2, "name": "Sales"}
]

# ==========================================
# 1. GET Endpoints (3 endpoints)
# ==========================================

# GET 1: 全従業員の取得
@app.get("/employees/", response_model=List[dict], tags=["GET"])
def get_all_employees():
    return db_employees

# GET 2: 特定の従業員をIDで取得
@app.get("/employees/{emp_id}", response_model=dict, tags=["GET"])
def get_employee_by_id(emp_id: int):
    emp = next((e for e in db_employees if e["id"] == emp_id), None)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    return emp

# GET 3: 特定の部署に所属する従業員の取得
@app.get("/departments/{dept_id}/employees", response_model=List[dict], tags=["GET"])
def get_employees_by_department(dept_id: int):
    return [e for e in db_employees if e["department_id"] == dept_id]


# ==========================================
# 2. POST Endpoints (3 endpoints)
# ==========================================

# POST 1: 新規従業員の作成
@app.post("/employees/", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED, tags=["POST"])
def create_employee(emp: EmployeeCreate):
    new_id = max([e["id"] for e in db_employees] + [0]) + 1
    new_emp = emp.model_dump()
    new_emp["id"] = new_id
    new_emp["is_active"] = True
    db_employees.append(new_emp)
    return new_emp

# POST 2: 新規部署の作成
@app.post("/departments/", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED, tags=["POST"])
def create_department(dept: DepartmentCreate):
    new_id = max([d["id"] for d in db_departments] + [0]) + 1
    new_dept = dept.model_dump()
    new_dept["id"] = new_id
    db_departments.append(new_dept)
    return new_dept

# POST 3: 従業員へのメモ/コメントの追加（擬似的なサブリソース作成）
@app.post("/employees/{emp_id}/notes", tags=["POST"])
def add_employee_note(emp_id: int, note: str):
    emp = next((e for e in db_employees if e["id"] == emp_id), None)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    # ここではDBに保存する代わりにレスポンスのみ返します
    return {"employee_id": emp_id, "note": note, "status": "Note added successfully"}


# ==========================================
# 3. DELETE Endpoints (3 endpoints)
# ==========================================

# DELETE 1: 従業員の削除
@app.delete("/employees/{emp_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["DELETE"])
def delete_employee(emp_id: int):
    global db_employees
    initial_length = len(db_employees)
    db_employees = [e for e in db_employees if e["id"] != emp_id]
    if len(db_employees) == initial_length:
        raise HTTPException(status_code=404, detail="Employee not found")

# DELETE 2: 部署の削除
@app.delete("/departments/{dept_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["DELETE"])
def delete_department(dept_id: int):
    global db_departments
    initial_length = len(db_departments)
    db_departments = [d for d in db_departments if d["id"] != dept_id]
    if len(db_departments) == initial_length:
        raise HTTPException(status_code=404, detail="Department not found")

# DELETE 3: 従業員の顔写真（または特定のリソース）の削除
@app.delete("/employees/{emp_id}/photo", status_code=status.HTTP_204_NO_CONTENT, tags=["DELETE"])
def delete_employee_photo(emp_id: int):
    emp = next((e for e in db_employees if e["id"] == emp_id), None)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    # 実際はここで画像ファイルを削除する処理が入ります
    return


# ==========================================
# 4. BATCH Endpoints (3 endpoints)
# ==========================================
# BATCH処理はPOSTやPUTメソッドにリスト(List)を渡す形で実装します。

# BATCH 1: 従業員の一括作成 (POST)
@app.post("/batch/employees/create", response_model=List[EmployeeResponse], status_code=status.HTTP_201_CREATED, tags=["BATCH"])
def batch_create_employees(employees: List[EmployeeCreate]):
    created_employees = []
    current_max_id = max([e["id"] for e in db_employees] + [0])
    
    for i, emp in enumerate(employees):
        new_emp = emp.model_dump()
        new_emp["id"] = current_max_id + i + 1
        new_emp["is_active"] = True
        db_employees.append(new_emp)
        created_employees.append(new_emp)
        
    return created_employees

# BATCH 2: 従業員の一括削除 (POST ※DELETEメソッドはボディを持つべきではないためPOSTを使用)
@app.post("/batch/employees/delete", tags=["BATCH"])
def batch_delete_employees(request: BatchDeleteRequest):
    global db_employees
    ids_to_delete = set(request.employee_ids)
    db_employees = [e for e in db_employees if e["id"] not in ids_to_delete]
    
    return {"message": f"Deleted employees with IDs: {list(ids_to_delete)}"}

# BATCH 3: 従業員のステータス一括更新 (PUT)
@app.put("/batch/employees/status", tags=["BATCH"])
def batch_update_employee_status(updates: List[BatchStatusUpdate]):
    updated_ids = []
    
    # 渡されたリストを元にループ処理で一括更新
    for update in updates:
        emp = next((e for e in db_employees if e["id"] == update.employee_id), None)
        if emp:
            emp["is_active"] = update.is_active
            updated_ids.append(update.employee_id)
            
    return {"message": "Batch update successful", "updated_employee_ids": updated_ids}
