from typing import Any
from uuid import uuid4
import re

from pydantic import UUID4, BaseModel, EmailStr, Field, ValidationError, field_serializer, field_validator, model_serializer

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

app = FastAPI()

VALID_NAME_REGEX = re.compile(r"^[a-zA-Z]{2,}$")

# Definindo os modelos de dados para a escola e os alunos, utilizando Pydantic para validação e serialização.

class Student(BaseModel):
    # Configuração para proibir campos extras e armazenar os alunos criados
    model_config = {
        "extra": "forbid",
    }
    __students__ = []

    # Definindo os campos do modelo Student, incluindo validação e exemplos
    id: UUID4 = Field(default_factory=uuid4, description="Unique identifier", kw_only=True)
    name: str = Field(examples=["Example"])
    email: EmailStr = Field(
        examples=["user@arjancodes.com"],
        description="The email address of the user",
        frozen=True,
    )   

    # Serializador para o campo id, convertendo o UUID4 para string ao serializar para JSON
    @field_serializer("id", when_used="json")
    def serialize_id(self, id: UUID4) -> str:
        return str(id)
    
    # Validador para o campo name, garantindo que o nome seja válido de acordo com a regex definida, ou seja, deve conter apenas letras e ter pelo menos 2 caracteres
    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not VALID_NAME_REGEX.match(v):
            raise ValueError(
                "Name is invalid, must contain only letters and be at least 2 characters long"
            )
        return v
    

    
# Definindo o modelo de dados para a escola, que inclui uma lista de alunos. A escola também tem um ID único e um nome.    
class School(BaseModel):
    model_config = {
        "extra": "forbid",
    }
    __schools__ = []
    id: UUID4 = Field(default_factory=uuid4, description="Unique identifier", kw_only=True)
    name: str = Field(..., description="Name of the school")
    students: list[Student] = Field(default_factory=list, description="List of students")

    # Serializador para o campo students, convertendo a lista de objetos Student para uma lista de nomes, ignorando os outros campos dos alunos 
    @field_serializer("students", when_used="json")
    @classmethod
    def serialize_students(cls, v) -> list:
        return [student.name for student in v]
    
    # Serializador para o modelo School, que retorna um dicionário com o id, nome e lista de nomes dos alunos, caso não haja campos específicos de inclusão ou exclusão. Caso contrário, ele utiliza o serializador padrão.
    @model_serializer(mode="wrap", when_used="json")
    def serialize_school(self, serializer, info) -> dict[str, Any]:
        if not info.include and not info.exclude:
            return {"id": self.id, "name": self.name, "students": [student.name for student in self.students]}
        return serializer(self)

# Definindo as rotas da API utilizando FastAPI para criar escolas, listar escolas, obter detalhes de uma escola específica, listar os alunos de uma escola, criar alunos, listar alunos e associar um aluno a uma escola. Cada rota utiliza os modelos definidos para validação e serialização dos dados.

# Rota para criar uma nova escola
@app.post("/school", response_model=School)
async def create_school(school: School):
    School.__schools__.append(school)
    return school

# Rota para listar todas as escolas
@app.get("/school", response_model=list[School])
async def get_schools() -> list[School]:
    return list(School.__schools__)

# Rota para obter detalhes de uma escola específica, utilizando o ID da escola como parâmetro.
@app.get("/school/{school_id}", response_model=School)
async def get_school(school_id: UUID4) -> School | JSONResponse:
    try:
        return next((school for school in School.__schools__ if school.id == school_id))        
    except StopIteration:
        return JSONResponse(status_code=404, content={"message": "School not found"})

# Rota para listar os alunos de uma escola específica, utilizando o ID da escola como parâmetro. 
@app.get("/school/{school_id}/students", response_model=list[Student])
async def get_school_students(school_id: UUID4) -> list[Student] | JSONResponse:
    
    try:
        school = next((school for school in School.__schools__ if school.id == school_id))
        return school.students
    except StopIteration:
        return JSONResponse(status_code=404, content={"message": "School not found"})

# Rota para criar um novo aluno
@app.post("/student", response_model=Student)
async def create_student(student: Student):
    Student.__students__.append(student)
    return student

# Rota para listar todos os alunos
@app.get("/student", response_model=list[Student])
async def get_students() -> list[Student]:
    return list(Student.__students__)

# Rota para associar um aluno a uma escola, utilizando os IDs da escola e do aluno como parâmetros.    
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

# Rota para obter a escola de um aluno específico, utilizando o ID do aluno como parâmetro. Ele percorre todas as escolas e seus alunos para encontrar a escola associada ao aluno. 
@app.get("/student/{student_id}/school", response_model=School)
async def get_student_school(student_id: UUID4) -> School | JSONResponse:
    try:
        return next((school for school in School.__schools__ for student in school.students if student.id == student_id))
    except StopIteration:
        return JSONResponse(status_code=404, content={"message": "Student not found"})



def main() -> None:

        
    # Variáveis de teste para facilitar ao criar uma escola e alguns alunos 
    school_data = {
        "name": "Example School",
    }
    student_data = [
            {"name": "Alice", "email": "alice@example.com"},
            {"name": "Bob", "email": "bob@example.com"}
        ]

    with TestClient(app) as client:

        # Testando a criação de uma escola e alguns alunos, verificando se o código de resposta é 200 e imprimindo os resultados.
       
        response = client.post("/school", json=school_data)
        assert response.status_code == 200, "Response code should be 200"
        print(f"Created school {response.json()["name"]}")

        for student in student_data:
            response = client.post("/student", json=student)
            assert response.status_code == 200, "Response code should be 200"
            print(f"Created student: {response.json()}")

    with TestClient(app) as client:
        # Listando as escolas criadas     
        response = client.get(f"/school")
        school_id = response.json()[0]["id"] # Pegando o ID da primeira escola criada para usar nas próximas requisições
        print(f"All schools: {response.json()}")

        # Listando os alunos criados
        response = client.get(f"/student")
        print(f"All students: {response.json()}")
        student_id = response.json()[0]["id"] # Pegando o ID do primeiro aluno criado para usar nas próximas requisições

        # Associando o aluno à escola criada e verificando se a resposta é 200
        response = client.post(f"/school/{school_id}/student/{student_id}")
        assert response.status_code == 200, "Response code should be 200"

        # Listando os alunos de uma escola específica para verificar se o aluno foi associado corretamente 
        response = client.get(f"/school/{school_id}/students")
        assert response.status_code == 200, "Response code should be 200"
        assert response.json() == ["Alice"], "The students in the school should be Alice"
        print(f"Students in school: {response.json()}")


        # Listando a escola de um aluno específico para verificar se a associação foi feita corretamente, verificando se a resposta é 200 e imprimindo o resultado.
        response = client.get(f"/student/{student_id}/school")
        assert response.status_code == 200, "Response code should be 200"
        assert response.json()["name"] == "Example School", "The school of the student should be Example School"
        print(f"School of student: {response.json()}")

    
if __name__ == "__main__":
    main()