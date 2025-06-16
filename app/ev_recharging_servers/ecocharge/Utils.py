# Funções Úteis para as Conexões HTTP ---------------------------------------------------------------------------------------------------------

# Importando as Dependências:
from flask import jsonify
from requests.exceptions import RequestException, ConnectionError, Timeout, HTTPError # Exceções Para Problemas de Conexão.
import urllib3 # Exceções Para Problemas de Conexão.
import asyncio
import aiohttp

# Tratando as Exceções do "HTTP" e "aiohttp":
def handleHTTPExceptions(exception):
    if isinstance (exception, urllib3.exceptions.NewConnectionError, aiohttp.ClientConnectorError):
        return jsonify({"error": "Não Há Caminho Até o Servidor!"}), 502 # Erro 502: Bad Gateway.
    elif isinstance (exception, (urllib3.exceptions.MaxRetryError, ConnectionError), asyncio.TimeoutError):
        return jsonify({"error": "Servidor Alvo Está Indisponível!"}), 503 # Erro 503: Service Unavailable.
    elif isinstance (exception, Timeout):
        return jsonify({"error": "Timeout!"}), 504 # Erro 504: Gateway Timeout.
    elif isinstance (exception, HTTPError, aiohttp.ClientResponseError):
        status_code = exception.response.status_code if exception.response else 500 # Erro do HTTP ou Erro Genérico.
        reason = exception.response.reason if exception.response else "Erro Desconhecido" # Razão do Erro ou Razão Desconhecida.
        return jsonify({"error": f"Erro HTTP: '{reason}'"}), status_code
    elif isinstance (exception, RequestException, Exception):
        return jsonify({"error": "Erro Genérico!"}), 500 # Erro 500: Internal Server Error.
    else:
        return jsonify({"error": "Erro Desconhecido!"}), 500
