from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from model.produto import Pedido
from datetime import date

class EnderecoOut(BaseModel):
    cep: str
    logradouro: str
    complemento: str
    bairro: str
    localidade: str
    uf: str

class PedidoIn(BaseModel):
    nome_cliente: str
    produto: str
    data_evento: date
    cep: str

class PedidoOut(PedidoIn):
    id: int
    logradouro: str
    bairro: str
    cidade: str
    estado: str

    class Config:
        model_config = ConfigDict(from_attributes=True)
        from_attributes = True

class PedidoUpdate(BaseModel):
    nome_cliente: Optional[str] = None
    produto: Optional[str] = None
    data_evento: Optional[date] = None
    cep: Optional[str] = None