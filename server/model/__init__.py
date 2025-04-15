from sqlalchemy_utils import database_exists, create_database
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import os

# Importando os elementos definidos no modelo
from model.base import Base
from model.produto import Pedido

# Caminho para o banco de dados dentro do contêiner
db_path = "/data/"  # No contêiner Docker, usaremos o caminho relativo mapeado

# Garantir que o diretório de dados exista
if not os.path.exists(db_path): 
    os.makedirs(db_path) 

# Define a URL do banco de dados SQLite
db_url = 'sqlite:///%s/db.sqlite3' % db_path  # Caminho absoluto dentro do contêiner

# Cria a engine de conexão com o banco
engine = create_engine(db_url, echo=False)

# Instancia um criador de sessão com o banco
Session = sessionmaker(bind=engine)

# Cria o banco de dados se ele não existir
if not database_exists(engine.url):
    create_database(engine.url)

# Cria as tabelas, caso não existam
Base.metadata.create_all(engine)