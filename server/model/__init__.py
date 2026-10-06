"""SQLite local ou em volume Docker, preservando os dados existentes."""
import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from model.base import Base
from model.produto import Pedido

default_database = Path(__file__).resolve().parent.parent / "database" / "db.sqlite3"
database_path = Path(os.environ.get("DATABASE_PATH", str(default_database))).resolve()
database_path.parent.mkdir(parents=True, exist_ok=True)
engine = create_engine("sqlite:///" + database_path.as_posix())
Session = sessionmaker(bind=engine)
Base.metadata.create_all(engine)

# Migração aditiva para bancos existentes; pedidos antigos permanecem sem preço.
with engine.begin() as connection:
    columns = {row[1] for row in connection.exec_driver_sql("PRAGMA table_info(pedidos)")}
    if "valor_unitario_centavos" not in columns:
        connection.exec_driver_sql("ALTER TABLE pedidos ADD COLUMN valor_unitario_centavos INTEGER")
    if "quantidade" not in columns:
        connection.exec_driver_sql("ALTER TABLE pedidos ADD COLUMN quantidade INTEGER NOT NULL DEFAULT 1")
