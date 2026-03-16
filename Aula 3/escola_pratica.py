from uuid import uuid4

from pydantic import UUID4, BaseModel, EmailStr, Field, ValidationError, field_serializer

class Student(BaseModel):
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
    
class School(BaseModel):
    id: UUID4 = Field(default_factory=uuid4, description="Unique identifier", kw_only=True)
    name: str = Field(..., description="Name of the school")
    students: list[Student] = Field(default_factory=list, description="List of students")

    @field_serializer("id", when_used="json")
    def serialize_id(self, id: UUID4) -> str:
        return str(id)

def create_new_student(data: dict[str, Any]) -> None:
    try:
        student = Student.model_validate(data)
        return student
    except ValidationError as e:
        print("Student is invalid")
        for error in e.errors():
            print(error)

def create_new_school(data: dict[str, Any]) -> None:
    try:
        school = School.model_validate(data)
        return school
    except ValidationError as e:
        print("School is invalid")
        for error in e.errors():
            print(error)            



def main() -> None:
    data = {
        "school_name": "Escola Prática",
        "students": [
            {"name": "Alice", "email": "alice@example.com"},
            {"name": "Bob", "email": "bob@example.com"}
        ]
    }
    try:
        school = School.model_validate({"name": data["school_name"]})
    
        for student_data in data["students"]:
            student = Student.model_validate(student_data)
            school.students.append(student)
        print(school.model_dump())
    except ValidationError as e:
        print("Data is invalid")
        for error in e.errors():
            print(error)            

  

    


if __name__ == "__main__":
    main()