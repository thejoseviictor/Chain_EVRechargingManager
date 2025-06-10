# Funções Úteis para as Conexões HTTP ---------------------------------------------------------------------------------------------------------

# Importando as Dependências:
import os
from flask import jsonify
import json
import requests
from requests.exceptions import RequestException, ConnectionError, Timeout, HTTPError # Exceções Para Problemas de Conexão.
import urllib3 # Exceções Para Problemas de Conexão.

# Tratando as Exceções do HTTP:
def handleHTTPExceptions(exception):
    if isinstance (exception, urllib3.exceptions.NewConnectionError):
        return jsonify({"error": "Não Há Caminho Até o Servidor!"}), 502 # Erro 502: Bad Gateway.
    elif isinstance (exception, (urllib3.exceptions.MaxRetryError, ConnectionError)):
        return jsonify({"error": "Servidor Alvo Está Indisponível!"}), 503 # Erro 503: Service Unavailable.
    elif isinstance (exception, Timeout):
        return jsonify({"error": "Timeout!"}), 504 # Erro 504: Gateway Timeout.
    elif isinstance (exception, HTTPError):
        status_code = exception.response.status_code if exception.response else 500 # Erro do HTTP ou Erro Genérico.
        reason = exception.response.reason if exception.response else "Erro Desconhecido" # Razão do Erro ou Razão Desconhecida.
        return jsonify({"error": f"Erro HTTP: '{reason}'"}), status_code
    elif isinstance (exception, RequestException):
        return jsonify({"error": "Erro Genérico!"}), 500 # Erro 500: Internal Server Error.
    else:
        return jsonify({"error": "Erro Desconhecido!"}), 500

# Envia as Reservas Destinadas aos Outros Servidores:
# 1. Envia Para o Primeiro Servidor da Lista de Rotas de Reserva.
# 2. Ele Faz as Reservas Pertencentes aos Seus Postos e Repassa as Outras Para o Próximo, Se Necessário.
# 3. As Reservas Efetuadas Retornarão Recursivamente.
def sendReservationsToOtherServers(data: json, reservationsRoute: list):
    try:
        data["reservationsRoute"] = reservationsRoute # Atualizando as Rotas do JSON, Que Será Enviado Para o Outro Servidor.
        # As Informações das Reservas Realizadas Irão Retornar Recursivamente:
        otherCompanyName = reservationsRoute[0]["company"] # Nome da Outra Empresa da Primeira Cidade da Rota.
        print("Redirecionando a Solicitação...\n")
        OTHER_SERVER_IP = os.environ.get(f'{otherCompanyName.upper()}_SERVER_IP') # Variável de Ambiente do Docker Compose.
        OTHER_SERVER_PORT = os.environ.get(f'{otherCompanyName.upper()}_SERVER_PORT') # Variável de Ambiente do Docker Compose.
        otherServerReservations = requests.post(f'http://{OTHER_SERVER_IP}:{OTHER_SERVER_PORT}/reservation', json=data, timeout=5)
        return jsonify(otherServerReservations.json()), otherServerReservations.status_code # Retornando a Resposta do Outro Servidor em Flask.
    # Tratando as Exceções:
    except Exception as e:
        return handleHTTPExceptions(e)
