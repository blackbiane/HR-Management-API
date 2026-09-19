from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field
from typing import List

app = FastAPI(
    title="HR API with Authentication and Validation",
    description="HR Management API including login functionality, token authentication, and validation (Regex and numerical ranges) with expanded mock data."
)

# ==========================================
# Security & Authentication (OAuth2)
# ==========================================
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

mock_users_db = {
    "admin": {"username": "admin", "password": "password123"}
}

def get_current_user(token: str = Depends(oauth2_scheme)):
    if not token.startswith("fake-token-"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"user": token.replace("fake-token-", "")}

# ==========================================
# Pydantic Models (Data Validation)
# ==========================================
class EmployeeCreate(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=50, example="John")
    last_name: str = Field(..., min_length=1, max_length=50, example="Doe")
    email: EmailStr = Field(..., example="john.doe@example.com")
    employee_code: str = Field(..., pattern=r"^EMP-\d{4}$", example="EMP-1234", description="Starts with EMP- followed by 4 digits")
    tel_number: str = Field(..., pattern=r"^0\d{1,4}-\d{1,4}-\d{4}$", example="090-1234-5678", description="Japanese phone number format")
    department_id: int = Field(..., ge=1, le=999, example=1, description="Department ID must be between 1 and 999")
    age: int = Field(..., ge=18, le=65, example=30, description="Age must be between 18 and 65")

class EmployeeResponse(EmployeeCreate):
    id: int
    is_active: bool

class DepartmentCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, example="Engineering")

class DepartmentResponse(DepartmentCreate):
    id: int

class BatchDeleteRequest(BaseModel):
    employee_ids: List[int] = Field(..., description="List of employee IDs to delete")

class BatchStatusUpdate(BaseModel):
    employee_id: int = Field(..., ge=1, description="Valid employee ID (1 or greater)")
    is_active: bool

# ==========================================
# Mock Database (Expanded Data)
# ==========================================
db_departments = [
    {"id": 1, "name": "Engineering"},
    {"id": 2, "name": "Sales"},
    {"id": 3, "name": "Human Resources"},
    {"id": 4, "name": "Marketing"},
    {"id": 5, "name": "Finance"},
    {"id": 6, "name": "Customer Support"},
    {"id": 7, "name": "Legal"},
    {"id": 8, "name": "Research and Development"},
    {"id": 9, "name": "Operations"},
    {"id": 10, "name": "IT Support"}
]

db_employees = [
    {"id": 1, "first_name": "John", "last_name": "Doe", "email": "john.doe@example.com", "employee_code": "EMP-0001", "tel_number": "03-1234-5678", "department_id": 1, "age": 28, "is_active": True},
    {"id": 2, "first_name": "Jane", "last_name": "Smith", "email": "jane.smith@example.com", "employee_code": "EMP-0002", "tel_number": "090-1111-2222", "department_id": 2, "age": 32, "is_active": True},
    {"id": 3, "first_name": "Alice", "last_name": "Johnson", "email": "alice.j@example.com", "employee_code": "EMP-0003", "tel_number": "080-3333-4444", "department_id": 3, "age": 25, "is_active": True},
    {"id": 4, "first_name": "Bob", "last_name": "Brown", "email": "bob.brown@example.com", "employee_code": "EMP-0004", "tel_number": "03-9876-5432", "department_id": 4, "age": 45, "is_active": True},
    {"id": 5, "first_name": "Charlie", "last_name": "Davis", "email": "charlie.d@example.com", "employee_code": "EMP-0005", "tel_number": "050-5555-6666", "department_id": 5, "age": 50, "is_active": True},
    {"id": 6, "first_name": "Eve", "last_name": "White", "email": "eve.white@example.com", "employee_code": "EMP-0006", "tel_number": "090-7777-8888", "department_id": 6, "age": 22, "is_active": True},
    {"id": 7, "first_name": "Frank", "last_name": "Miller", "email": "frank.m@example.com", "employee_code": "EMP-0007", "tel_number": "03-4444-5555", "department_id": 7, "age": 38, "is_active": False},
    {"id": 8, "first_name": "Grace", "last_name": "Wilson", "email": "grace.w@example.com", "employee_code": "EMP-0008", "tel_number": "080-9999-0000", "department_id": 8, "age": 29, "is_active": True},
    {"id": 9, "first_name": "Harry", "last_name": "Taylor", "email": "harry.t@example.com", "employee_code": "EMP-0009", "tel_number": "090-2222-3333", "department_id": 9, "age": 60, "is_active": True},
    {"id": 10, "first_name": "Ivy", "last_name": "Thomas", "email": "ivy.thomas@example.com", "employee_code": "EMP-0010", "tel_number": "03-7777-1111", "department_id": 10, "age": 34, "is_active": True}
]

# ==========================================
# 0. Auth Endpoints
# ==========================================
@app.post("/login", tags=["Authentication"])
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = mock_users_db.get(form_data.username)
    if not user or user["password"] != form_data.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"access_token": f"fake-token-{user['username']}", "token_type": "bearer"}

# ==========================================
# 1. GET Endpoints
# ==========================================
@app.get("/employees/", response_model=List[EmployeeResponse], tags=["GET"])
def get_all_employees(current_user: dict = Depends(get_current_user)):
    return db_employees

@app.get("/employees/{emp_id}", response_model=EmployeeResponse, tags=["GET"])
def get_employee_by_id(emp_id: int = Field(..., ge=1), current_user: dict = Depends(get_current_user)):
    emp = next((e for e in db_employees if e["id"] == emp_id), None)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    return emp

@app.get("/departments/{dept_id}/employees", response_model=List[EmployeeResponse], tags=["GET"])
def get_employees_by_department(dept_id: int = Field(..., ge=1, le=999), current_user: dict = Depends(get_current_user)):
    return [e for e in db_employees if e["department_id"] == dept_id]

# ==========================================
# 2. POST Endpoints
# ==========================================
@app.post("/employees/", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED, tags=["POST"])
def create_employee(emp: EmployeeCreate, current_user: dict = Depends(get_current_user)):
    new_id = max([e["id"] for e in db_employees] + [0]) + 1
    new_emp = emp.model_dump()
    new_emp.update({"id": new_id, "is_active": True})
    db_employees.append(new_emp)
    return new_emp

@app.post("/departments/", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED, tags=["POST"])
def create_department(dept: DepartmentCreate, current_user: dict = Depends(get_current_user)):
    new_id = max([d["id"] for d in db_departments] + [0]) + 1
    new_dept = dept.model_dump()
    new_dept["id"] = new_id
    db_departments.append(new_dept)
    return new_dept

@app.post("/employees/{emp_id}/notes", tags=["POST"])
def add_employee_note(emp_id: int = Field(..., ge=1), note: str = Field(..., min_length=1), current_user: dict = Depends(get_current_user)):
    emp = next((e for e in db_employees if e["id"] == emp_id), None)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    return {"employee_id": emp_id, "note": note, "status": "Note added successfully"}

# ==========================================
# 3. DELETE Endpoints
# ==========================================
@app.delete("/employees/{emp_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["DELETE"])
def delete_employee(emp_id: int = Field(..., ge=1), current_user: dict = Depends(get_current_user)):
    global db_employees
    initial_length = len(db_employees)
    db_employees = [e for e in db_employees if e["id"] != emp_id]
    if len(db_employees) == initial_length:
        raise HTTPException(status_code=404, detail="Employee not found")

@app.delete("/departments/{dept_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["DELETE"])
def delete_department(dept_id: int = Field(..., ge=1, le=999), current_user: dict = Depends(get_current_user)):
    global db_departments
    initial_length = len(db_departments)
    db_departments = [d for d in db_departments if d["id"] != dept_id]
    if len(db_departments) == initial_length:
        raise HTTPException(status_code=404, detail="Department not found")

@app.delete("/employees/{emp_id}/photo", status_code=status.HTTP_204_NO_CONTENT, tags=["DELETE"])
def delete_employee_photo(emp_id: int = Field(..., ge=1), current_user: dict = Depends(get_current_user)):
    emp = next((e for e in db_employees if e["id"] == emp_id), None)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    return

# ==========================================
# 4. BATCH Endpoints
# ==========================================
@app.post("/batch/employees/create", response_model=List[EmployeeResponse], status_code=status.HTTP_201_CREATED, tags=["BATCH"])
def batch_create_employees(employees: List[EmployeeCreate], current_user: dict = Depends(get_current_user)):
    created_employees = []
    current_max_id = max([e["id"] for e in db_employees] + [0])
    
    for i, emp in enumerate(employees):
        new_emp = emp.model_dump()
        new_emp.update({"id": current_max_id + i + 1, "is_active": True})
        db_employees.append(new_emp)
        created_employees.append(new_emp)
        
    return created_employees

@app.post("/batch/employees/delete", tags=["BATCH"])
def batch_delete_employees(request: BatchDeleteRequest, current_user: dict = Depends(get_current_user)):
    global db_employees
    ids_to_delete = set(request.employee_ids)
    db_employees = [e for e in db_employees if e["id"] not in ids_to_delete]
    return {"message": f"Deleted employees with IDs: {list(ids_to_delete)}"}

@app.put("/batch/employees/status", tags=["BATCH"])
def batch_update_employee_status(updates: List[BatchStatusUpdate], current_user: dict = Depends(get_current_user)):
    updated_ids = []
    for update in updates:
        emp = next((e for e in db_employees if e["id"] == update.employee_id), None)
        if emp:
            emp["is_active"] = update.is_active
            updated_ids.append(update.employee_id)
            
    return {"message": "Batch update successful", "updated_employee_ids": updated_ids}
