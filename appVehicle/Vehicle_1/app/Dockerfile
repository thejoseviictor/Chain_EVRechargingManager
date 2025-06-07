
# Imagem base para a "build" da imagem atual
FROM python:3.13.3

# Define o diretório principal
WORKDIR /app

# Instala todos os pacotes/bibliotecas externas definidos no arquivo "requirements.txt" e sem cache local
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# Copia o projeto inteiro, respeitando o .dockerignore
COPY . .

# Define os comandos e parâmetros
CMD ["python", "main.py"]