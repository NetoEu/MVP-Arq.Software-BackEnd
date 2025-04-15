# Backend - API para Controle de Pedidos

Este repositório contém a API desenvolvida com **Flask** e **Flask-OpenAPI3**, oferecendo funcionalidades de controle de produtos, comentários, pedidos de clientes e consulta de endereços via CEP. A API segue a arquitetura **RESTful** e é estruturada para facilitar a integração com o frontend e outros sistemas.

## Funcionalidades principais:

### 🔸 **Documentação interativa:**
- Acesso à documentação interativa da API através das ferramentas **Swagger**, **Redoc** e **RapiDoc** via rota raiz (`/`).

### 🔸 **CEP:**
- **Consulta de endereço via CEP:** `/api/cep/<cep>`  
  - Realiza uma consulta ao serviço **ViaCEP** para recuperar o endereço completo de um CEP.

### 🔸 **Pedidos:**
- **Criação de pedido:** `/api/pedido` (POST)  
  - Permite criar um pedido, preenchendo automaticamente o endereço a partir do CEP informado.
- **Listagem de pedidos:** `/api/pedido` (GET)  
  - Recupera todos os pedidos registrados no sistema.
- **Exclusão de pedido:** `/api/pedido/<int:pedido_id>` (DELETE)  
  - Exclui um pedido com base no seu ID.

## 🔧 **Tecnologias utilizadas:**
- **Flask** - Framework web utilizado para construção da API.
- **Flask-OpenAPI3** - Para documentação interativa da API.
- **SQLAlchemy** - ORM utilizado para interação com o banco de dados.
- **Pydantic** - Para validação dos dados de entrada e saída da API.
- **Flask-CORS** - Suporte a requisições **cross-origin** (CORS).

## 🔐 **Respostas da API**
A API segue o modelo definido em **schemas.py** para garantir a padronização das respostas, tornando a integração com o frontend mais eficiente.

---

## Como rodar a API

### Requisitos:
- Python 3.x
- Dependências descritas no `requirements.txt`

### Passos para rodar a API:

1. Clone o repositório:
   ```bash
   git clone https://github.com/seuusuario/projeto-api.git
   cd projeto-api
