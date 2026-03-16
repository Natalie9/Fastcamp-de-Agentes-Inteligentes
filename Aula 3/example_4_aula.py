from datetime import datetime
from typing import Optional
from uuid import uuid4

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from pydantic import BaseModel, EmailStr, Field, field_serializer, UUID4

app = FastAPI()


class User(BaseModel):
    """
    Aqui é trabalhado o fastAPI.
    A classe User que é o basemodel é declarada.
    Model_config com extra: forbid.
    Declaração dos mesmos campos anteriores, mas agora adicionando o campo Friends 
    que é uma lista de ids, com no máximo 500 itens.
    Lista de bloqueados, de assinaturas (signup_ts) e o próprio id.
    """
    model_config = {
        "extra": "forbid",
    }
    __users__ = []
    name: str = Field(..., description="Name of the user")
    email: EmailStr = Field(..., description="Email address of the user")
    friends: list[UUID4] = Field(
        default_factory=list, max_items=500, description="List of friends"
    )
    blocked: list[UUID4] = Field(
        default_factory=list, max_items=500, description="List of blocked users"
    )
    signup_ts: Optional[datetime] = Field(
        default_factory=datetime.now, description="Signup timestamp", kw_only=True
    )
    id: UUID4 = Field(
        default_factory=uuid4, description="Unique identifier", kw_only=True
    )

    @field_serializer("id", when_used="json")
    def serialize_id(self, id: UUID4) -> str:
        """
        O campo id tem um serializer próprio de uuid4 para string.
        """
        return str(id)


@app.get("/users", response_model=list[User])
async def get_users() -> list[User]:
    """
    Com fastAPI é criado rotas http, como get de /users que retorna uma lista de usuários.
    """
    return list(User.__users__)


@app.post("/users", response_model=User)
async def create_user(user: User):
    """
    Post /users que faz um append em user.
    """
    User.__users__.append(user)
    return user


@app.get("/users/{user_id}", response_model=User)
async def get_user(user_id: UUID4) -> User | JSONResponse:
    """
    O get user/id chama uma função next buscando o usuário com o id correspondente.
    """
    try:
        return next((user for user in User.__users__ if user.id == user_id))
    except StopIteration:
        return JSONResponse(status_code=404, content={"message": "User not found"})


def main() -> None:
    """
    No main tem um TestClient(app) as client: -- estrutura para testar a aplicação.
    Tem um for de 5 vezes usando um cliente pra chamar post de usuários, criando os 5.
    Faz um assert conferindo se teve response == 200.
    Uma sequencia de asserts que parece tipo uns ifelse validando.
    Depois dessa sequencia de asserts no json do response ele chama um user.model_validate com o json.
    Depois mais uma sequencia de asserts.
    Depois faz um get de users/id.
    Novos asserts, um conferindo se o nome é User 5 respondendo que é o usuário mais novo.
    """
    with TestClient(app) as client:
        for i in range(5):
            response = client.post(
                "/users",
                json={"name": f"User {i}", "email": f"example{i}@arjancodes.com"},
            )
            assert response.status_code == 200
            assert response.json()["name"] == f"User {i}", (
                "The name of the user should be User {i}"
            )
            assert response.json()["id"], "The user should have an id"

            user = User.model_validate(response.json())
            assert str(user.id) == response.json()["id"], "The id should be the same"
            assert user.signup_ts, "The signup timestamp should be set"
            assert user.friends == [], "The friends list should be empty"
            assert user.blocked == [], "The blocked list should be empty"

        response = client.get("/users")
        assert response.status_code == 200, "Response code should be 200"
        assert len(response.json()) == 5, "There should be 5 users"

        response = client.post(
            "/users", json={"name": "User 5", "email": "example5@arjancodes.com"}
        )
        assert response.status_code == 200
        assert response.json()["name"] == "User 5", (
            "The name of the user should be User 5"
        )
        assert response.json()["id"], "The user should have an id"

        user = User.model_validate(response.json())
        assert str(user.id) == response.json()["id"], "The id should be the same"
        assert user.signup_ts, "The signup timestamp should be set"
        assert user.friends == [], "The friends list should be empty"
        assert user.blocked == [], "The blocked list should be empty"

        response = client.get(f"/users/{response.json()['id']}")
        assert response.status_code == 200
        assert response.json()["name"] == "User 5", (
            "This should be the newly created user"
        )

        response = client.get(f"/users/{uuid4()}")
        assert response.status_code == 404
        assert response.json()["message"] == "User not found", (
            "We technically should not find this user"
        )

        response = client.post("/users", json={"name": "User 6", "email": "wrong"})
        assert response.status_code == 422, "The email address is should be invalid"


if __name__ == "__main__":
    main()
