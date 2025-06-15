# Funções Administrativas do "Owner" da Blockchain Ganache ----------------------------------------------------

# Importando as Dependências:
import os
from flask import Flask, request, jsonify
from web3 import Web3
import time
from Utils import sendContractsAddresses
from ContractUtils import deployContract, authorizeServer

# Criando a Aplicação Flask:
app = Flask(__name__)

# Salvando o IP e Porta Da API Owner:
OWNER_IP = os.environ.get('OWNER_IP')
OWNER_PORT = int(os.environ.get('OWNER_PORT'))

# Salvando as Informações do Ganache:
GANACHE_URL = os.environ.get('GANACHE_URL')
ECOCHARGE_ACCOUNT = int(os.environ.get('ECOCHARGE_ACCOUNT'))
EFLUX_ACCOUNT = int(os.environ.get('EFLUX_ACCOUNT'))
VOLTPOINT_ACCOUNT = int(os.environ.get('VOLTPOINT_ACCOUNT'))

# Salvando o IP e Porta Das API dos Servidores das Empresas:
ECOCHARGE_SERVER_IP = os.environ.get('ECOCHARGE_SERVER_IP')
ECOCHARGE_SERVER_PORT = int(os.environ.get('ECOCHARGE_SERVER_PORT'))
EFLUX_SERVER_IP = os.environ.get('EFLUX_SERVER_IP')
EFLUX_SERVER_PORT = int(os.environ.get('EFLUX_SERVER_PORT'))
VOLTPOINT_SERVER_IP = os.environ.get('VOLTPOINT_SERVER_IP')
VOLTPOINT_SERVER_PORT = int(os.environ.get('VOLTPOINT_SERVER_PORT'))

# Conectando ao Ganache e Web3:
while True:
    try:
        w3 = Web3(Web3.HTTPProvider(GANACHE_URL))
        if not w3.is_connected():
            raise Exception("Não foi Possível Conectar-se Ao Ganache!\n")
        print("Conectado ao Ganache!\n")
        break
    except Exception as e:
        print(f"Erro de Conexão ao Ganache: {e}\n")
        time.sleep(3) # Tempo de Espera Para Tentar uma Nova Conexão.

# Configurando as Contas do Ganache:
owner_account = w3.eth.accounts[0]
ecocharge_account = w3.eth.accounts[ECOCHARGE_ACCOUNT]
eflux_account = w3.eth.accounts[EFLUX_ACCOUNT]
voltpoint_account = w3.eth.accounts[VOLTPOINT_ACCOUNT]

# Implementando e Recebendo os Endereços dos Contratos:
as_contract = deployContract(w3, owner_account, "AuthorizedServers") # Servidores Autorizados.
rl_contract = deployContract(w3, owner_account, "ReservationLedger", as_contract.address) # Reservas.
escrow_contract = deployContract(w3, owner_account, "Escrow", as_contract.address, rl_contract.address) # Escrow de Pagamento.
cs_contract = deployContract(w3, owner_account, "ChargingSession", as_contract.address, rl_contract.address, escrow_contract.address) # Sessão de Carregamento.

# Salvando os Endereços dos Contratos em Um Dicionário Para Enviar aos Servidores das Empresas:
contractsAddresses = {
    "ReservationLedger": rl_contract.address,
    "Escrow": escrow_contract.address,
    "ChargingSession": cs_contract.address
}

# Autorizando os Servidores das Empresas no Contrato "AuthorizedServers":
authorizeServer(w3, as_contract, owner_account, ECOCHARGE_ACCOUNT)
authorizeServer(w3, as_contract, owner_account, EFLUX_ACCOUNT)
authorizeServer(w3, as_contract, owner_account, VOLTPOINT_ACCOUNT)

# FINALIZAR!
# Enviando os Endereços dos Contratos Para os Servidores das Empresas:
sendContractsAddresses(ECOCHARGE_SERVER_IP, ECOCHARGE_SERVER_PORT, contractsAddresses)
sendContractsAddresses(EFLUX_SERVER_IP, EFLUX_SERVER_PORT, contractsAddresses)
sendContractsAddresses(VOLTPOINT_SERVER_IP, VOLTPOINT_SERVER_PORT, contractsAddresses)

# Iniciando a API (Flask) Para Enviar Informações dos Contratos Para os Servidores das Empresas:
if __name__ == '__main__':
    app.run(host=OWNER_IP, port=OWNER_PORT, debug=True)
