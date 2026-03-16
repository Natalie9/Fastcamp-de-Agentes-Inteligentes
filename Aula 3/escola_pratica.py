from typing import Any
from uuid import uuid4
import re

from pydantic import UUID4, BaseModel, EmailStr, Field, ValidationError, field_serializer, field_validator, model_serializer

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

app = FastAPI()


VALID_NAME_REGEX = re.compile(r"^[a-zA-Z]{2,}$")


class Student(BaseModel):
    model_config = {
        "extra": "forbid",
    }
    __students__ = []

    id: UUID4 = Field(default_factory=uuid4, description="Unique identifier", kw_only=True)
    name: str = Field(examples=["Example"])
    email: EmailStr = Field(
        examples=["user@arjancodes.com"],
        description="The email address of the user",
        frozen=True,
    )   

    @field_serializer("id", when_used="json")
    def serialize_id(self, id: UUID4) -> str:
        return str(id)
    
    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not VALID_NAME_REGEX.match(v):
            raise ValueError(
                "Name is invalid, must contain only letters and be at least 2 characters long"
            )
        return v
    

    
    
class School(BaseModel):
    model_config = {
        "extra": "forbid",
    }
    __schools__ = []
    id: UUID4 = Field(default_factory=uuid4, description="Unique identifier", kw_only=True)
    name: str = Field(..., description="Name of the school")
    students: list[Student] = Field(default_factory=list, description="List of students")

    @field_serializer("students", when_used="json")
    @classmethod
    def serialize_students(cls, v) -> list:
        return [student.name for student in v]
    

    @model_serializer(mode="wrap", when_used="json")
    def serialize_school(self, serializer, info) -> dict[str, Any]:
        if not info.include and not info.exclude:
            return {"id": self.id, "name": self.name, "students": [student.name for student in self.students]}
        return serializer(self)


@app.post("/school", response_model=School)
async def create_school(school: School):
    School.__schools__.append(school)
    return school

@app.get("/school", response_model=list[School])
async def get_schools() -> list[School]:
    return list(School.__schools__)

@app.get("/school/{school_id}", response_model=School)
async def get_school(school_id: UUID4) -> School | JSONResponse:
    try:
        return next((school for school in School.__schools__ if school.id == school_id))        
    except StopIteration:
        return JSONResponse(status_code=404, content={"message": "School not found"})
    
@app.get("/school/{school_id}/students", response_model=list[Student])
async def get_school_students(school_id: UUID4) -> list[Student] | JSONResponse:
    
    try:
        school = next((school for school in School.__schools__ if school.id == school_id))
        return school.students
    except StopIteration:
        return JSONResponse(status_code=404, content={"message": "School not found"})

@app.post("/student", response_model=Student)
async def create_student(student: Student):
    Student.__students__.append(student)
    return student

@app.get("/student", response_model=list[Student])
async def get_students() -> list[Student]:
    return list(Student.__students__)
    
@app.post("/school/{school_id}/student/{student_id}", response_model=School)
async def create_school_student(school_id: UUID4, student_id: UUID4) -> School | JSONResponse:
    print(f"Adding student {student_id} to school {school_id}")
    try:
        school = next((school for school in School.__schools__ if school.id == school_id))
        print(f"Found school {school.name}")

        student = next((student for student in Student.__students__ if student.id == student_id))
        print(f"Found student {student}")

        school.students.append(student)
        return school
    
    except StopIteration:
        return JSONResponse(status_code=404, content={"message": "School not found"})    
    
@app.get("/student/{student_id}/school", response_model=School)
async def get_student_school(student_id: UUID4) -> School | JSONResponse:
    try:
        return next((school for school in School.__schools__ for student in school.students if student.id == student_id))
    except StopIteration:
        return JSONResponse(status_code=404, content={"message": "Student not found"})



def main() -> None:
    school_data = {
        "name": "Example School",
    }
    student_data = [
            {"name": "Alice", "email": "alice@example.com"},
            {"name": "Bob", "email": "bob@example.com"}
        ]

    with TestClient(app) as client:

        response = client.post("/school", json=school_data)
        assert response.status_code == 200, "Response code should be 200"
        print(f"Created school {response.json()["name"]}")

        for student in student_data:
            response = client.post("/student", json=student)
            assert response.status_code == 200, "Response code should be 200"
            print(f"Created student: {response.json()}")

    with TestClient(app) as client:
        response = client.get(f"/school")
        school_id = response.json()[0]["id"]
        print(f"All schools: {response.json()}")

        response = client.get(f"/student")
        print(f"All students: {response.json()}")
        student_id = response.json()[0]["id"]

        response = client.post(f"/school/{school_id}/student/{student_id}")
        assert response.status_code == 200, "Response code should be 200"

        response = client.get(f"/school")
        school_id = response.json()[0]["id"]
        print(f"All schools: {response.json()}")

        response = client.get(f"/school/{school_id}/students")
        assert response.status_code == 200, "Response code should be 200"
        print(f"Students in school: {response.json()}")

        response = client.get(f"/student/{student_id}/school")
        assert response.status_code == 200, "Response code should be 200"
        print(f"School of student: {response.json()}")


        

           
            

    
if __name__ == "__main__":
    main()