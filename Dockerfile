# Etapa 1: Definindo a imagem base
FROM python:3.12-slim

# Etapa 2: Instalando dependências do sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    && apt-get clean

# Etapa 3: Definindo o diretório de trabalho
WORKDIR /app

# Copia todo o conteúdo da pasta do projeto (incluindo a pasta server) para o diretório /app no container
COPY . /app

# Etapa 4: Instalando dependências do Python
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Etapa 5: Copiando o código do projeto para o contêiner
COPY . .

# Etapa 6: Expondo a porta 5000 (padrão para o Flask)
EXPOSE 5000

# Etapa 7: Comando para rodar o Flask
CMD ["python", "server/app.py"]