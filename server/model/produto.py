from sqlalchemy import Column, String, Integer, DateTime, Float, Date
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Union

from model import Base

class Pedido(Base):
    __tablename__ = 'pedidos'

    id = Column(Integer, primary_key=True)
    nome_cliente = Column(String, nullable=False)
    produto = Column(String, nullable=False)
    data_evento = Column(Date, nullable=False)
    cep = Column(String, nullable=False)
    logradouro = Column(String)
    bairro = Column(String)
    cidade = Column(String)
    estado = Column(String)
