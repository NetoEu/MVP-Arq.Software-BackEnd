# API de Controle de Pedidos

API REST em Python/Flask para cadastrar, listar, editar e excluir pedidos com data de evento e endereço consultado pelo CEP. Usa SQLAlchemy e SQLite para persistência e Flask-OpenAPI3 para documentar todas as operações.

`requirements.txt` declara as dependências diretas e aplica as versões transitivas verificadas em `requirements.lock`.

## Pré-requisitos e arquivos necessários

| Item | Sem Docker | Com Docker |
|---|---|---|
| Python 3.12 com pip e venv | Instalar na máquina | Fornecido pela imagem do backend |
| Docker com Compose | Não necessário | Instalar e iniciar antes dos comandos |
| Git | Necessário apenas para clonar; dispensável se os arquivos já estão na máquina | Mesma condição |
| Navegador e acesso à internet | Navegador para Swagger/interface; internet para instalar dependências e consultar ViaCEP | Mesma condição, incluindo download das imagens |
| SQLite | Suporte incluído no Python; arquivo criado pela aplicação | Incluído no container |

`requirements.txt` não instala Python, Docker, Git nem arquivos do projeto. Ele instala as bibliotecas Python. Mantenha também `requirements.lock` na mesma pasta, pois o requirements o referencia. O código de `server/`, os Dockerfiles e os arquivos Compose devem acompanhar o repositório. Não é necessário instalar um servidor SQLite, Node.js ou um editor de código para executar.

## Execução com Docker

Requisito: Docker com Compose.

```sh
git clone https://github.com/NetoEu/MVP-Arq.Software-BackEnd.git backEnd
cd backEnd
docker compose up --build
```

API: http://localhost:5000. Swagger: http://localhost:5000/openapi/swagger.

O Compose monta `server/database` em `/data`. O arquivo `db.sqlite3` permanece na máquina após parar ou recriar o container. SQLite não precisa de um container próprio. Para parar: `docker compose down`.

Para executar também a interface, use o Compose do [frontend](https://github.com/NetoEu/MVP-Arq.Software-FrontEnd), que inicia os dois serviços. Não execute os dois arquivos Compose simultaneamente, pois ambos publicam a porta 5000.

## Execução local

Requisito: Python 3.12. Abra o terminal na pasta `backEnd`. Os comandos abaixo funcionam no Prompt de Comando (CMD) e no PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe server/app.py
```

No Linux/macOS, use `.venv/bin/python` nos dois últimos comandos. Por padrão, o banco fica em `server/database/db.sqlite3`, independentemente do diretório de execução. A variável `DATABASE_PATH` permite escolher outro arquivo. Um banco inexistente será criado; não há migração ou exclusão automática dos registros existentes.

### Se aparecer “python não é reconhecido”

Se `.venv\Scripts\python.exe` já existir (como no ambiente local preparado neste projeto), não recrie o ambiente. Execute diretamente, dentro de `backEnd`:

```cmd
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe server\app.py
```

Em uma máquina nova, verifique se o launcher está disponível com `py -3.12 --version`. Se estiver, crie o ambiente com `py -3.12 -m venv .venv`. Caso nem `python` nem `py` estejam disponíveis, instale Python 3.12 com pip e a opção de adicionar Python ao PATH; feche e reabra o terminal. Depois execute novamente os comandos de criação e instalação. A pasta `.venv` é local, não acompanha o Git e não deve ser copiada entre computadores.

Mantenha o terminal da API aberto. Acesse http://localhost:5000/openapi/swagger, expanda uma rota e selecione **Try it out**, preencha os parâmetros/corpo e clique em **Execute**. Para listar diretamente no navegador: http://localhost:5000/api/pedido. Para consultar um CEP: http://localhost:5000/api/cep/01001000. POST, PUT e DELETE devem ser acionados pelo Swagger, pela interface ou por um cliente HTTP. Use o ID retornado pelo cadastro/listagem para editar ou excluir. Para encerrar o servidor, pressione **Ctrl+C**.

## Rotas

Os corpos de criação e atualização também aceitam `valor_unitario_centavos` (inteiro de 0 a 100.000.000) e `quantidade` (inteiro de 1 a 10.000). Exemplo: `"valor_unitario_centavos": 8500, "quantidade": 3` representa três unidades de R$ 85,00. O preço é informado pelo operador na interface; não há catálogo de preços imposto pela API. A omissão mantém compatibilidade com clientes antigos (preço não informado e quantidade 1 na criação).

Na inicialização, uma migração aditiva inclui essas colunas em bancos SQLite anteriores, preservando os registros. Preços anteriores não são inferidos do catálogo. O total é calculado multiplicando os centavos pela quantidade.

| Método | Rota | Função |
|---|---|---|
| GET | `/api/cep/{cep}` | Consulta endereço no ViaCEP |
| POST | `/api/pedido` | Cria pedido; retorna 201 |
| GET | `/api/pedido` | Lista por data do evento e ID |
| PUT | `/api/pedido/{pedido_id}` | Atualiza os campos enviados |
| DELETE | `/api/pedido/{pedido_id}` | Exclui um pedido |

Corpo de exemplo para POST (PUT aceita um subconjunto desses campos):

```json
{"nome_cliente":"Maria","produto":"Bolo de aniversário","data_evento":"2026-10-15","cep":"01001000"}
```

Nome e produto devem conter entre 1 e 200 caracteres após remover espaços das extremidades. CEP deve conter oito dígitos. A data usa `AAAA-MM-DD`, sem horário. Não envie `null` na edição; omita o campo para manter seu valor. A API obtém o endereço diretamente do ViaCEP e o recalcula quando o CEP muda.

Erros: 422 para entrada inválida, 404 para pedido/CEP inexistente, 502 para falha ou resposta inválida do ViaCEP, 504 para timeout e 500 para falha de persistência. Erros de negócio usam `{"erro":"mensagem"}`; validações 422 usam o formato do Flask-OpenAPI3. Transações são revertidas em caso de falha e as sessões são fechadas.

## Serviço externo

Consulta: `GET https://viacep.com.br/ws/{cep}/json/`. Serviço gratuito, sem chave ou cadastro para essa consulta. Documentação e condições: https://viacep.com.br/. A página consultada não declara uma licença específica para redistribuir a base; o projeto apenas consulta endereços e não distribui a base. O provedor alerta que consultas massivas podem causar bloqueio. Há limites de espera de 3,05 segundos para conexão e 10 segundos para leitura.

## Testes

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Os testes usam SQLite temporário e simulam o ViaCEP. Cobrem CRUD, persistência, troca de CEP, validação, indisponibilidade, rollback e presença das cinco operações no OpenAPI. Não modificam o banco real.

### Certificados HTTPS em redes com proxy

Se o ambiente retornar `CERTIFICATE_VERIFY_FAILED`, configure `REQUESTS_CA_BUNDLE` com o caminho de um arquivo PEM contendo as autoridades certificadoras confiáveis da sua rede/sistema. Exemplo no PowerShell: `$env:REQUESTS_CA_BUNDLE = 'C:\certificados\autoridades.pem'`. O arquivo deve ser fornecido ou validado pelo responsável pela rede; não desative a verificação TLS. Em Docker, o arquivo também precisa estar montado no container e a variável deve apontar para o caminho interno correspondente.

No CMD, antes de iniciar a API, use `set "REQUESTS_CA_BUNDLE=C:\certificados\autoridades.pem"`. Substitua pelo caminho de um arquivo existente. Essa configuração é específica do ambiente e não é uma dependência instalável pelo requirements.

Somente nesta máquina, foi preparado o arquivo `tmp/system-ca.pem` na pasta principal do projeto com autoridades já confiáveis pelo Windows. Enquanto esse arquivo existir, partindo de `backEnd`, é possível usar:

```cmd
set "REQUESTS_CA_BUNDLE=%CD%\..\tmp\system-ca.pem"
.venv\Scripts\python.exe server\app.py
```

Esse arquivo temporário não acompanha os repositórios e não é requisito geral do projeto. Em outra máquina, configure certificados apenas se necessário, usando as autoridades confiáveis daquele ambiente.

## Organização

- `server/app.py`: rotas e integração ViaCEP.
- `server/model`: modelo e conexão SQLite.
- `server/schemas`: validação e contratos OpenAPI.
- `tests`: testes de regressão.
- `Dockerfile` e `docker-compose.yml`: execução em container.

Ambientes virtuais, caches e bancos locais não devem ser versionados. O servidor Flask utilizado é adequado à demonstração acadêmica; a configuração não inclui autenticação ou implantação de produção.
