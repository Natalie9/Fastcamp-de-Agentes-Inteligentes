from enum import auto, IntFlag
from typing import Any

from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    SecretStr,
    ValidationError,
)


class Role(IntFlag):
    """
    Classe Role criando tipo author, editor, developer e Admin que pode assumir um dos cargos anteriores
    """
    Author = auto()
    Editor = auto()
    Developer = auto()
    Admin = Author | Editor | Developer


class User(BaseModel):
    """
    Classe User com atributos de nome, email, senha e role
    Os atributos possuem um tipo, e nas propriedades de campo é possível colocar um exemplo (estilo placeholder), 
    descrição e se deve estar congelado (frozen), tbm uma opção padrão
    """
    name: str = Field(examples=["Arjan"])
    email: EmailStr = Field(
        examples=["example@arjancodes.com"],
        description="The email address of the user",
        frozen=True,
    )
    password: SecretStr = Field(
        examples=["Password123"], description="The password of the user"
    )
    role: Role = Field(default=None, description="The role of the user")


def validate(data: dict[str, Any]) -> None:
    """
    Definido método de validação, recebe parâmetro data como um dicionário. 
    Nessa função tenta enviar em User.model_validate(data), ou dá erro de que usuário é inválido
    """
    try:
        user = User.model_validate(data)
        print(user)
    except ValidationError as e:
        print("User is invalid")
        for error in e.errors():
            print(error)


def main() -> None:
    """
    No método main cria-se 2 exemplos de teste, um com dados corretos pra um novo usuário 
    e outro com email inválido.
    """
    good_data = {
        "name": "Arjan",
        "email": "example@arjancodes.com",
        "password": "Password123",
    }
    bad_data = {"email": "<bad data>", "password": "<bad data>"}

    validate(good_data)
    validate(bad_data)


if __name__ == "__main__":
    main()
