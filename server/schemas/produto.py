from datetime import date
from typing import Annotated
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

Texto = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
Cep = Annotated[str, StringConstraints(pattern=r"^[0-9]{8}$")]

class PedidoPath(BaseModel):
    pedido_id: int = Field(gt=0)

class CepPath(BaseModel):
    cep: Cep

class EnderecoOut(BaseModel):
    cep: str
    logradouro: str = ""
    complemento: str = ""
    bairro: str = ""
    localidade: str
    uf: str

class PedidoIn(BaseModel):
    nome_cliente: Texto
    produto: Texto
    data_evento: date
    cep: Cep
    valor_unitario_centavos: int | None = Field(default=None, ge=0, le=100000000, strict=True)
    quantidade: int = Field(default=1, ge=1, le=10000, strict=True)

class PedidoOut(PedidoIn):
    model_config = ConfigDict(from_attributes=True)
    id: int
    logradouro: str | None = None
    bairro: str | None = None
    cidade: str | None = None
    estado: str | None = None

class PedidoUpdate(BaseModel):
    nome_cliente: Texto | None = None
    produto: Texto | None = None
    data_evento: date | None = None
    cep: Cep | None = None
    valor_unitario_centavos: int | None = Field(default=None, ge=0, le=100000000, strict=True)
    quantidade: int | None = Field(default=None, ge=1, le=10000, strict=True)

    @field_validator("nome_cliente", "produto", "data_evento", "cep", "quantidade", mode="before")
    @classmethod
    def rejeitar_nulo(cls, value):
        if value is None:
            raise ValueError("Omita o campo em vez de enviar null.")
        return value
