"""Testes isolados: nenhum dado real ou chamada externa é utilizado."""
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

temporary = tempfile.TemporaryDirectory()
os.environ["DATABASE_PATH"] = str(Path(temporary.name) / "test.sqlite3")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))
import app as api
from model import Base, Session, Pedido, engine
from sqlalchemy.exc import SQLAlchemyError

ADDRESS = {"cep": "01001-000", "logradouro": "Praça da Sé", "bairro": "Sé", "localidade": "São Paulo", "uf": "SP"}
PAYLOAD = {"nome_cliente": "Cliente teste", "produto": "Bolo", "data_evento": "2026-10-15", "cep": "01001000"}

class ApiTest(unittest.TestCase):
    def setUp(self):
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)
        api.app.config["TESTING"] = True
        self.client = api.app.test_client()
        self.mock = patch.object(api.requests, "get").start()
        self.addCleanup(patch.stopall)
        self.mock.return_value = Mock(json=Mock(return_value=ADDRESS))

    def criar(self):
        response = self.client.post("/api/pedido", json=PAYLOAD)
        self.assertEqual(response.status_code, 201, response.json)
        return response.json["id"]

    def test_crud_and_persistence(self):
        pedido_id = self.criar()
        response = self.client.get("/api/pedido")
        self.assertEqual(response.json[0]["data_evento"], "2026-10-15")
        with Session() as session:
            self.assertEqual(session.get(Pedido, pedido_id).cidade, "São Paulo")
        self.mock.reset_mock()
        response = self.client.put(f"/api/pedido/{pedido_id}", json={"produto": "Doces"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["produto"], "Doces")
        self.mock.assert_not_called()
        self.assertEqual(self.client.delete(f"/api/pedido/{pedido_id}").status_code, 200)
        self.assertEqual(self.client.get("/api/pedido").json, [])

    def test_changed_cep_updates_address(self):
        pedido_id = self.criar()
        self.mock.return_value.json.return_value = {**ADDRESS, "cep": "20040-020", "localidade": "Rio de Janeiro", "uf": "RJ"}
        response = self.client.put(f"/api/pedido/{pedido_id}", json={"cep": "20040020"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["cidade"], "Rio de Janeiro")

    def test_invalid_input_does_not_call_external_service(self):
        for changes in [{"cep": "abc12345"}, {"nome_cliente": " "}, {"data_evento": "2026-02-30"}]:
            self.assertEqual(self.client.post("/api/pedido", json={**PAYLOAD, **changes}).status_code, 422)
        self.assertEqual(self.client.get("/api/cep/abc").status_code, 422)
        self.mock.assert_not_called()

    def test_update_rejects_null(self):
        pedido_id = self.criar()
        self.assertEqual(self.client.put(f"/api/pedido/{pedido_id}", json={"produto": None}).status_code, 422)

    def test_price_quantity_persist_and_update(self):
        response = self.client.post("/api/pedido", json={**PAYLOAD, "valor_unitario_centavos": 350, "quantidade": 12})
        self.assertEqual(response.status_code, 201)
        pedido_id = response.json["id"]
        self.assertEqual(self.client.get("/api/pedido").json[0]["quantidade"], 12)
        response = self.client.put(f"/api/pedido/{pedido_id}", json={"quantidade": 20, "valor_unitario_centavos": 400})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["valor_unitario_centavos"] * response.json["quantidade"], 8000)

    def test_invalid_price_quantity(self):
        for changes in [{"quantidade": 0}, {"quantidade": 1.5}, {"quantidade": None}, {"quantidade": True}, {"valor_unitario_centavos": -1}, {"valor_unitario_centavos": 1.5}]:
            self.assertEqual(self.client.post("/api/pedido", json={**PAYLOAD, **changes}).status_code, 422)

    def test_legacy_price_is_unknown(self):
        self.criar()
        pedido = self.client.get("/api/pedido").json[0]
        self.assertIsNone(pedido["valor_unitario_centavos"])
        self.assertEqual(pedido["quantidade"], 1)

    def test_missing_order(self):
        self.assertEqual(self.client.put("/api/pedido/999", json={"produto": "Bolo"}).status_code, 404)
        self.assertEqual(self.client.delete("/api/pedido/999").status_code, 404)

    def test_external_failures_and_atomic_update(self):
        pedido_id = self.criar()
        for error, status in [(api.requests.Timeout(), 504), (api.requests.ConnectionError(), 502), (ValueError(), 502)]:
            self.mock.side_effect = error
            self.assertEqual(self.client.get("/api/cep/01001000").status_code, status)
            self.assertEqual(self.client.post("/api/pedido", json=PAYLOAD).status_code, status)
            response = self.client.put(f"/api/pedido/{pedido_id}", json={"nome_cliente": "Não salvar", "cep": "20040020"})
            self.assertEqual(response.status_code, status)
        self.assertEqual(self.client.get("/api/pedido").json[0]["nome_cliente"], PAYLOAD["nome_cliente"])
        self.assertEqual(len(self.client.get("/api/pedido").json), 1)

    def test_unknown_and_malformed_address(self):
        for data, status in [({"erro": True}, 404), ({"erro": "true"}, 404), ({}, 502), ([], 502)]:
            self.mock.return_value.json.return_value = data
            self.assertEqual(self.client.get("/api/cep/01001000").status_code, status)

    def test_cep_timeout_and_response(self):
        response = self.client.get("/api/cep/01001000")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["localidade"], "São Paulo")
        self.mock.assert_called_once_with("https://viacep.com.br/ws/01001000/json/", timeout=(3.05, 10))

    def test_database_error_rolls_back(self):
        with patch("sqlalchemy.orm.Session.flush", side_effect=SQLAlchemyError("falha interna")):
            response = self.client.post("/api/pedido", json=PAYLOAD)
        self.assertEqual(response.status_code, 500)
        self.assertNotIn("falha interna", response.json["erro"])
        self.assertEqual(self.client.get("/api/pedido").json, [])
        self.criar()

    def test_openapi_contains_every_business_operation(self):
        response = self.client.get("/openapi/openapi.json")
        self.assertEqual(response.status_code, 200)
        paths = response.json["paths"]
        for path, methods in {"/api/pedido": ["get", "post"], "/api/pedido/{pedido_id}": ["put", "delete"], "/api/cep/{cep}": ["get"]}.items():
            for method in methods:
                self.assertIn(method, paths[path])
        self.assertEqual(self.client.get("/").status_code, 302)
        self.assertEqual(self.client.get("/openapi/swagger").status_code, 200)

def tearDownModule():
    engine.dispose()
    temporary.cleanup()

if __name__ == "__main__":
    unittest.main()
