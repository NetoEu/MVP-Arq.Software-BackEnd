from flask_openapi3 import OpenAPI, Info, Tag
from flask import redirect, request, jsonify
from urllib.parse import unquote
from sqlalchemy.exc import IntegrityError
from model import Session, Pedido
from schemas import *
from flask_cors import CORS, cross_origin
import requests

info = Info(title="Minha API", version="1.0.0")
app = OpenAPI(__name__, info=info)
CORS(app)

home_tag = Tag(name="Documentação", description="Seleção de documentação: Swagger, Redoc ou RapiDoc")
cep_tag = Tag(name="CEP", description="Busca de endereço pelo CEP")
pedido_tag = Tag(name="Pedido", description="Operações relacionadas a pedidos")

@app.get("/", tags=[home_tag])
def home():
    return redirect('/openapi'), 200

@app.route("/api/cep/<cep>", methods=["GET"])
def buscar_cep(cep):
    try:
        response = requests.get(f"https://viacep.com.br/ws/{cep}/json/")
        data = response.json()
        if "erro" in data:
            return jsonify({"error": "CEP não encontrado"}), 404
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.post("/api/pedido")
def criar_pedido(body: PedidoIn):
    # Busca o endereço pelo CEP
    response = requests.get(f"https://viacep.com.br/ws/{body.cep}/json/")  # Verifica se o CEP é válido
    data = response.json()

    if "erro" in data:
        return jsonify({"error": "CEP não encontrado"}), 404

    novo_pedido = Pedido(
        nome_cliente=body.nome_cliente,
        produto=body.produto,
        data_evento=body.data_evento,
        cep=body.cep,
        logradouro=data.get("logradouro"),
        bairro=data.get("bairro"),
        cidade=data.get("localidade"),
        estado=data.get("uf")
    )

    session = Session()
    session.add(novo_pedido)
    session.commit()

    # Converte PedidoOut para dicionário e retorna como resposta JSON
    return jsonify(PedidoOut.from_orm(novo_pedido).dict())

# Endpoint para listar todos os pedidos
@app.get("/api/pedido", tags=[pedido_tag])
def listar_pedidos():
    session = Session()
    pedidos = session.query(Pedido).all()
    result = [PedidoOut.model_validate(pedido, from_attributes=True).model_dump() for pedido in pedidos]
    session.close()
    return jsonify(result)

@app.route("/api/pedido/<int:pedido_id>", methods=["DELETE"])
@cross_origin()
def deletar_pedido(pedido_id):
    try:
        session = Session()
        pedido = session.get(Pedido, pedido_id)
        if not pedido:
            session.close()
            return jsonify({"erro": "Pedido não encontrado"}), 404

        session.delete(pedido)
        session.commit()
        session.close()
        return jsonify({"mensagem": "Pedido deletado com sucesso"})
    except Exception as e:
        return jsonify({"erro": f"Ocorreu um erro ao tentar excluir o pedido: {str(e)}"}), 500
    
@app.put("/api/pedido/<int:pedido_id>", tags=[pedido_tag])
def atualizar_pedido(pedido_id: int, body: PedidoUpdate):
    try:
        session = Session()
        pedido = session.get(Pedido, pedido_id)

        if not pedido:
            return jsonify({"erro": "Pedido não encontrado"}), 404

        # Atualiza os campos se estiverem no body
        if body.nome_cliente is not None:
            pedido.nome_cliente = body.nome_cliente

        if body.produto is not None:
            pedido.produto = body.produto

        if body.data_evento is not None:
            pedido.data_evento = body.data_evento

        if body.cep is not None and body.cep != pedido.cep:
            response = requests.get(f"https://viacep.com.br/ws/{body.cep}/json/")
            endereco = response.json()
            if "erro" in endereco:
                return jsonify({"erro": "Novo CEP inválido"}), 400

            pedido.cep = body.cep
            pedido.logradouro = endereco.get("logradouro", "")
            pedido.bairro = endereco.get("bairro", "")
            pedido.cidade = endereco.get("localidade", "")
            pedido.estado = endereco.get("uf", "")

        session.commit()
        return PedidoOut.from_orm(pedido), 200

    except Exception as e:
        return jsonify({"erro": f"Erro ao atualizar pedido: {str(e)}"}), 500
    finally:
        session.close()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
