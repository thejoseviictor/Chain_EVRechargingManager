# Funções Administrativas do "Owner" da Blockchain Ganache ----------------------------------------------------

# Importando as Dependências:
import os
from flask import Flask, request, jsonify
from web3 import Web3
import time
from Utils import sendContractsAddresses
from ContractUtils import implementContract

# Criando a Aplicação Flask:
app = Flask(__name__)

# Salvando o IP e Porta Da API Owner:
OWNER_IP = os.environ.get('OWNER_IP')
OWNER_PORT = int(os.environ.get('OWNER_PORT'))

# Salvando o IP e Porta Das API dos Servidores das Empresas:
ECOCHARGE_SERVER_IP = os.environ.get('ECOCHARGE_SERVER_IP')
ECOCHARGE_SERVER_PORT = int(os.environ.get('ECOCHARGE_SERVER_PORT'))
EFLUX_SERVER_IP = os.environ.get('EFLUX_SERVER_IP')
EFLUX_SERVER_PORT = int(os.environ.get('EFLUX_SERVER_PORT'))
VOLTPOINT_SERVER_IP = os.environ.get('VOLTPOINT_SERVER_IP')
VOLTPOINT_SERVER_PORT = int(os.environ.get('VOLTPOINT_SERVER_PORT'))

# Salvando as Informações do Ganache:
GANACHE_URL = os.environ.get('GANACHE_URL')
ECOCHARGE_ACCOUNT = int(os.environ.get('ECOCHARGE_ACCOUNT'))
EFLUX_ACCOUNT = int(os.environ.get('EFLUX_ACCOUNT'))
VOLTPOINT_ACCOUNT = int(os.environ.get('VOLTPOINT_ACCOUNT'))

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

if w3:
    # Configurando as Contas do Ganache:
    accounts = w3.eth.accounts
    owner_account = accounts[0]
    ecocharge_account = accounts[ECOCHARGE_ACCOUNT]
    eflux_account = accounts[EFLUX_ACCOUNT]
    voltpoint_account = accounts[VOLTPOINT_ACCOUNT]

    # Implementando e Recebendo os Endereços dos Contratos:
    escrow_address = implementContract(w3, owner_account, "app/contracts/", "app/contracts/")
    recharging_ledger_address = implementContract(w3, owner_account, "app/contracts/", "app/contracts/")
    reservation_ledger_address = implementContract(w3, owner_account, "app/contracts/", "app/contracts/")
    print(f"Contrato 'Escrow' Implantado em: {escrow_address}\n")
    print(f"Contrato 'RechargingLedger' Implantado em: {recharging_ledger_address}\n")
    print(f"Contrato 'ReservationLedger' Implantado em: {reservation_ledger_address}\n")

    # Salvando os Endereços dos Contratos em Um Dicionário:
    contractsAddresses = {
        "Escrow": escrow_address,
        "RechargingLedger": recharging_ledger_address,
        "ReservationLedger": reservation_ledger_address
    }

    # Enviando os Endereços dos Contratos Para os Servidores das Empresas:
    sendContractsAddresses(ECOCHARGE_SERVER_IP, ECOCHARGE_SERVER_PORT, contractsAddresses)
    sendContractsAddresses(EFLUX_SERVER_IP, EFLUX_SERVER_PORT, contractsAddresses)
    sendContractsAddresses(VOLTPOINT_SERVER_IP, VOLTPOINT_SERVER_PORT, contractsAddresses)

# Iniciando a API (Flask) Para Enviar Informações dos Contratos Para os Servidores das Empresas:
if __name__ == '__main__':
    app.run(host=OWNER_IP, port=OWNER_PORT, debug=True)
