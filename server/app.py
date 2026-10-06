"""API de pedidos com documentação OpenAPI e integração ViaCEP."""
import requests
from flask import redirect
from flask_cors import CORS
from flask_openapi3 import Info, OpenAPI, Tag
from pydantic import BaseModel, RootModel
from sqlalchemy.exc import SQLAlchemyError
from model import Pedido, Session
from schemas.error import ErrorSchema
from schemas.produto import CepPath, EnderecoOut, PedidoIn, PedidoOut, PedidoPath, PedidoUpdate

app = OpenAPI(__name__, info=Info(title="API de Controle de Pedidos", version="1.1.0"))
CORS(app)
pedido_tag = Tag(name="Pedidos", description="Cadastro, consulta, edição e exclusão")
cep_tag = Tag(name="CEP", description="Endereços consultados no ViaCEP")

class Mensagem(BaseModel):
    mensagem: str

class ListaPedidos(RootModel[list[PedidoOut]]):
    pass

class ErroCEP(Exception):
    def __init__(self, mensagem, status):
        self.mensagem = mensagem
        self.status = status

@app.errorhandler(ErroCEP)
def erro_cep(error):
    return {"erro": error.mensagem}, error.status

@app.errorhandler(SQLAlchemyError)
def erro_banco(error):
    app.logger.exception("Falha ao acessar o banco de dados")
    return {"erro": "Não foi possível concluir a operação no banco de dados."}, 500

def consultar_cep(cep):
    try:
        response = requests.get(f"https://viacep.com.br/ws/{cep}/json/", timeout=(3.05, 10))
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict):
            raise ValueError("Resposta inválida")
        if data.get("erro"):
            raise ErroCEP("CEP não encontrado.", 404)
        return EnderecoOut.model_validate(data)
    except requests.Timeout as error:
        raise ErroCEP("A consulta de CEP demorou demais. Tente novamente.", 504) from error
    except (requests.RequestException, ValueError) as error:
        raise ErroCEP("O serviço de CEP está indisponível. Tente novamente.", 502) from error

def aplicar_endereco(pedido, endereco):
    pedido.logradouro = endereco.logradouro
    pedido.bairro = endereco.bairro
    pedido.cidade = endereco.localidade
    pedido.estado = endereco.uf

def apresentar(pedido):
    return PedidoOut.model_validate(pedido).model_dump(mode="json")

@app.get("/", doc_ui=False)
def home():
    return redirect("/openapi")

@app.get("/api/cep/<cep>", tags=[cep_tag], responses={200: EnderecoOut, 404: ErrorSchema, 502: ErrorSchema, 504: ErrorSchema})
def buscar_cep(path: CepPath):
    """Consulta um CEP com oito dígitos."""
    return consultar_cep(path.cep).model_dump(mode="json")

@app.post("/api/pedido", tags=[pedido_tag], responses={201: PedidoOut, 404: ErrorSchema, 502: ErrorSchema, 504: ErrorSchema})
def criar_pedido(body: PedidoIn):
    """Cria um pedido e preenche o endereço pelo ViaCEP."""
    endereco = consultar_cep(body.cep)
    with Session.begin() as session:
        pedido = Pedido(**body.model_dump())
        aplicar_endereco(pedido, endereco)
        session.add(pedido)
        session.flush()
        result = apresentar(pedido)
    return result, 201

@app.get("/api/pedido", tags=[pedido_tag], responses={200: ListaPedidos})
def listar_pedidos():
    """Lista os pedidos em ordem de data do evento e identificador."""
    with Session() as session:
        return [apresentar(p) for p in session.query(Pedido).order_by(Pedido.data_evento, Pedido.id).all()]

@app.put("/api/pedido/<int:pedido_id>", tags=[pedido_tag], responses={200: PedidoOut, 404: ErrorSchema, 502: ErrorSchema, 504: ErrorSchema})
def atualizar_pedido(path: PedidoPath, body: PedidoUpdate):
    """Atualiza os campos informados; um novo CEP atualiza o endereço."""
    with Session.begin() as session:
        pedido = session.get(Pedido, path.pedido_id)
        if pedido is None:
            return {"erro": "Pedido não encontrado."}, 404
        changes = body.model_dump(exclude_unset=True)
        if "cep" in changes and changes["cep"] != pedido.cep:
            aplicar_endereco(pedido, consultar_cep(changes["cep"]))
        for key, value in changes.items():
            setattr(pedido, key, value)
        session.flush()
        result = apresentar(pedido)
    return result

@app.delete("/api/pedido/<int:pedido_id>", tags=[pedido_tag], responses={200: Mensagem, 404: ErrorSchema})
def deletar_pedido(path: PedidoPath):
    """Exclui um pedido pelo identificador."""
    with Session.begin() as session:
        pedido = session.get(Pedido, path.pedido_id)
        if pedido is None:
            return {"erro": "Pedido não encontrado."}, 404
        session.delete(pedido)
    return {"mensagem": "Pedido excluído com sucesso."}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
