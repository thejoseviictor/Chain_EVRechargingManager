# Funções Administrativas do "Owner" da Blockchain Ganache ----------------------------------------------------------------------------------------------------

# Importando as Dependências:
import os
from flask import Flask, request, jsonify
from web3 import Web3
import time
from ContractUtils import deployContract, authorizeServer, finishChargingSession

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

# Dados Globais da Blockchain:
w3 = None
owner_account = None
ecocharge_account = None
eflux_account = None
voltpoint_account = None
contracts_addresses = {}

# Configurando a Blockchain:
def setupBlockchain():
    # Definindo as Variáveis Globais:
    global w3, owner_account, ecocharge_account, eflux_account, voltpoint_account, contracts_addresses

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
    csm_contract = deployContract(w3, owner_account, "ChargingSessionManager", as_contract.address, rl_contract.address, escrow_contract.address) # Sessão de Carregamento.

    # Salvando os Endereços dos Contratos em Um Dicionário Para Enviar aos Servidores das Empresas:
    contracts_addresses = {
        "ReservationLedger": rl_contract.address,
        "Escrow": escrow_contract.address,
        "ChargingSessionManager": csm_contract.address
    }

    # Autorizando os Servidores das Empresas no Contrato "AuthorizedServers":
    authorizeServer(w3, as_contract, owner_account, ecocharge_account)
    authorizeServer(w3, as_contract, owner_account, eflux_account)
    authorizeServer(w3, as_contract, owner_account, voltpoint_account)

    # Armazenando o Contrato da Sessão de Carregamento Para Uso na Rota "/finish_cs":
    app.config["CSM_CONTRACT"] = csm_contract

# Rota Para Enviar os Endereços dos Contratos Deployados:
@app.route('/contracts', methods=['GET'])
def getContractsAddresses():
    return jsonify(contracts_addresses), 200

# Rota Para Finalizar uma Sessão de Carregamento e Liberar os Fundos do Pagamento ao Servidor Que Prestou o Serviço:
@app.route('/finish_cs', methods=['POST'])
def finishCS():
    # Tratando os Dados Recebidos:
    data = request.json # Recebendo os Dados em um Dicionário: data = {reservationID: int}.
    reservationID = data.get('reservationID') # ID da Reserva.
    # Solicitando a Finalização da Sessão de Carregamento na Blockchain:
    finished = finishChargingSession(w3, app.config["CSM_CONTRACT"], owner_account, reservationID)
    # Retornando:
    if finished:
        return f"Sucesso ao Finalizar a Sessão de Carregamento da Reserva '{reservationID}'", 200
    else:
        return jsonify({"error": "Erro Genérico!"}), 500

# Iniciando a Blockchain e API (Flask):
if __name__ == '__main__':
    setupBlockchain()
    app.run(host=OWNER_IP, port=OWNER_PORT, debug=True, use_reloader=False)
