from fastapi import FastAPI, HTTPException, status, File, UploadFile
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import date
import os
import shutil

# Create a directory to store uploaded photos
os.makedirs("static/photos", exist_ok=True)

# Initialize FastAPI app
app = FastAPI(
    title="HR Management API",
    description="Backend API for an HR Management Web Application (with photo upload support)",
    version="1.1.0"
)

# Mount the static directory to serve uploaded images via URL
app.mount("/static", StaticFiles(directory="static"), name="static")

# ==========================================
# Pydantic Models (Data Validation)
# ==========================================

class DepartmentBase(BaseModel):
    name: str = Field(..., example="Engineering")
    description: Optional[str] = Field(None, example="System development and maintenance")

class DepartmentCreate(DepartmentBase):
    pass

class DepartmentResponse(DepartmentBase):
    id: int
    class Config:
        from_attributes = True

class EmployeeBase(BaseModel):
    first_name: str = Field(..., example="John")
    last_name: str = Field(..., example="Doe")
    email: EmailStr = Field(..., example="john.doe@example.com")
    department_id: int = Field(..., example=1)
    hire_date: date = Field(..., example="2023-04-01")
    is_active: bool = Field(True, example=True)
    # Field for the profile photo URL
    photo_url: Optional[str] = Field(None, example="/static/photos/1_profile.png")

class EmployeeCreate(EmployeeBase):
    pass

class EmployeeUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    department_id: Optional[int] = None
    is_active: Optional[bool] = None

class EmployeeResponse(EmployeeBase):
    id: int
    class Config:
        from_attributes = True

# ==========================================
# In-Memory Mock Database
# ==========================================
fake_departments = [
    {"id": 1, "name": "Sales", "description": "Customer relations and sales management"},
    {"id": 2, "name": "Engineering", "description": "In-house service development and maintenance"}
]

fake_employees = [
    {
        "id": 1, "first_name": "John", "last_name": "Doe", 
        "email": "john.doe@example.com", "department_id": 1, 
        "hire_date": date(2020, 4, 1), "is_active": True,
        "photo_url": None
    }
]

# ==========================================
# API Endpoints
# ==========================================

@app.get("/departments/", response_model=List[DepartmentResponse], tags=["Departments"])
def get_departments():
    return fake_departments

@app.get("/employees/", response_model=List[EmployeeResponse], tags=["Employees"])
def get_employees(department_id: Optional[int] = None):
    # Filter by department_id if provided
    if department_id:
        return [emp for emp in fake_employees if emp["department_id"] == department_id]
    return fake_employees

@app.post("/employees/", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED, tags=["Employees"])
def create_employee(emp: EmployeeCreate):
    # Verify the department exists
    if not any(d["id"] == emp.department_id for d in fake_departments):
        raise HTTPException(status_code=400, detail="The specified department does not exist.")
    
    new_id = max([e["id"] for e in fake_employees] + [0]) + 1
    new_emp = emp.model_dump()
    new_emp["id"] = new_id
    fake_employees.append(new_emp)
    return new_emp

@app.get("/employees/{emp_id}", response_model=EmployeeResponse, tags=["Employees"])
def get_employee(emp_id: int):
    for emp in fake_employees:
        if emp["id"] == emp_id:
            return emp
    raise HTTPException(status_code=404, detail="Employee not found.")

# --- Photo Upload Endpoint ---
@app.post("/employees/{emp_id}/photo", response_model=EmployeeResponse, tags=["Employee Photos"])
def upload_employee_photo(emp_id: int, file: UploadFile = File(...)):
    # Verify the employee exists
    emp_index = next((index for index, e in enumerate(fake_employees) if e["id"] == emp_id), None)
    if emp_index is None:
        raise HTTPException(status_code=404, detail="Employee not found.")
    
    # Basic validation to ensure the file is an image
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Please upload an image file (e.g., jpeg, png).")

    # Generate the file path (e.g., static/photos/1_filename.png)
    file_location = f"static/photos/{emp_id}_{file.filename}"
    
    # Save the file locally
    with open(file_location, "wb+") as file_object:
        shutil.copyfileobj(file.file, file_object)
    
    # Update the employee record with the photo URL
    photo_url = f"/{file_location}"
    fake_employees[emp_index]["photo_url"] = photo_url
    
    return fake_employees[emp_index]
