# Funções Úteis para Contratos Solidity ---------------------------------------------------------

# Importando as Dependências:
import os
from web3 import Web3
import time
import json
import requests
from ReservationsManager import ReservationsManager

# Caminho dos Contratos:
CONTRACTS_DIR = 'build/contracts/'

# Salvando as Informações do Owner:
OWNER_IP = os.environ.get(f'OWNER_IP')
OWNER_PORT = int(os.environ.get(f'OWNER_PORT'))

# Carregando o "ABI" de Um Contrato Compilado:
def getContractData(contract_name: str):
    with open(f"{CONTRACTS_DIR}{contract_name}.abi", 'r') as abi_file:
        abi = json.loads(abi_file.read()) # Lendo Como Dicionário.
    return abi

# Conectando ao Ganache e Web3:
def connectGanacheWeb3(GANACHE_URL: str):
    while True:
        try:
            w3 = Web3(Web3.HTTPProvider(GANACHE_URL))
            if not w3.is_connected():
                raise Exception("Não foi Possível Conectar-se Ao Ganache!\n")
            print("Conectado ao Ganache!")
            return w3
        except Exception as e:
            print(f"Erro de Conexão ao Ganache: {e}\n")
            time.sleep(3) # Tempo de Espera Para Tentar uma Nova Conexão.

# Recebendo os Endereços dos Contratos Compilados:
def getContractsAddresses():
    try:
        response = requests.get(f'http://{OWNER_IP}:{OWNER_PORT}/contracts')
        print(f"Contratos Compilados Recebidos Com Sucesso!\n")
        return response.json()
    # Tratando as Exceções:
    except Exception as e:
        print(f"Erro ao Receber os Contratos Compilados: {e}\n")
        return None

# Criando uma Reserva "Pendente" na Blockchain:
def createReservationBlockchain(w3: Web3, rl_contract, server_account, vehicleID: int, data: dict):
    # Verificando os Dados:
    assert isinstance(data["startTimestamp"], int)
    assert isinstance(data["finishTimestamp"], int)
    assert Web3.is_address(data["customerAddress"]), "Endereço da Conta do Cliente Inválido!\n"
    assert Web3.is_address(server_account), "Endereço da Conta do Prestador de Serviço Inválido!\n"
    # Enviando os Dados:
    try:
        print(f"Criando uma Reserva na Blockchain Para '{vehicleID}' em '{data["cityCodename"]}'\n")
        tx_hash = rl_contract.functions.createReservation(
            data["chargingStationID"],
            data["chargingPointID"],
            data["cityCodename"],
            data["companyName"],
            data["startTimestamp"],
            data["finishTimestamp"],
            data["price"],
            data["customerAddress"],
            server_account
        ).transact({
            'from': server_account,
            "nonce": w3.eth.get_transaction_count(server_account),
            'gasPrice': w3.eth.gas_price,
            "gas": 230000,
            "chainId": w3.eth.chain_id
        })
        w3.eth.wait_for_transaction_receipt(tx_hash)
        return True
    except Exception as e:
        print(f"Erro ao Criar Uma Reserva na Blockchain Para '{vehicleID}' em '{data["cityCodename"]}: {e}\n")
        return None

# Iniciando Uma Sessão de Carregamento:
def startChargingSession(w3: Web3, csm_contract, server_account, reservationID: int):
    # Verificando os Dados:
    assert Web3.is_address(server_account), "Endereço da Conta do Prestador de Serviço Inválido!\n"
    # Enviando os Dados:
    try:
        print(f"Iniciando a Sessão de Carregamento da Reserva: {reservationID}\n")
        tx_hash = csm_contract.functions.startChargingSession(reservationID).transact({
            'from': server_account,
            "nonce": w3.eth.get_transaction_count(server_account),
            'gasPrice': w3.eth.gas_price,
            "gas": 100000,
            "chainId": w3.eth.chain_id
        })
        w3.eth.wait_for_transaction_receipt(tx_hash)
        # Verificando o Status da Sessão de Carregamento na Blockchain:
        cs = csm_contract.functions.getChargingSession(reservationID).call()
        cs_status = cs[2] # 0 = IDLE, 1 = IN_PROGRESS, 2 = FINISHED.
        if cs_status == 1:
            print(f"Sessão de Carregamento da Reserva '{reservationID}' Iniciada Com Sucesso!\n")
            return True
        else:
            print(f"Falha ao Iniciar a Sessão de Carregamento da Reserva '{reservationID}'!\n")
            return None
    except Exception as e:
        print(f"Erro ao Iniciar a Sessão de Carregamento da Reserva '{reservationID}': {e}\n")
        return None

# Finalizando Uma Sessão de Carregamento:
def finishChargingSession(w3: Web3, csm_contract, server_account, reservationID: int):
    # Verificando os Dados:
    assert Web3.is_address(server_account), "Endereço da Conta do Prestador de Serviço Inválido!\n"
    # Enviando os Dados:
    try:
        print(f"Finalizando a Sessão de Carregamento da Reserva: {reservationID}\n")
        tx_hash = csm_contract.functions.finishChargingSession(reservationID).transact({
            'from': server_account,
            "nonce": w3.eth.get_transaction_count(server_account),
            'gasPrice': w3.eth.gas_price,
            "gas": 47000,
            "chainId": w3.eth.chain_id
        })
        w3.eth.wait_for_transaction_receipt(tx_hash)
        # Verificando o Status da Sessão de Carregamento na Blockchain:
        cs = csm_contract.functions.getChargingSession(reservationID).call()
        cs_status = cs[2] # 0 = IDLE, 1 = IN_PROGRESS, 2 = FINISHED.
        if cs_status == 2:
            print(f"Sessão de Carregamento da Reserva '{reservationID}' Finalizada Com Sucesso!\n")
            return True
        else:
            print(f"Falha ao Finalizar a Sessão de Carregamento da Reserva '{reservationID}'!\n")
            return None
    except Exception as e:
        print(f"Erro ao Finalizar a Sessão de Carregamento da Reserva '{reservationID}': {e}\n")
        return None

# Marcando Todas as Reservas Pendentes de Um Usuário Como Confirmadas e Criando o Escrow:
def markReservationsAsConfirmed(w3: Web3, rl_contract, escrow_contract, server_account, customerAddress, company_accounts):
    # Verificando os Dados:
    assert Web3.is_address(customerAddress), "Endereço da Conta do Cliente Inválido!\n"
    assert Web3.is_address(server_account), "Endereço da Conta do Prestador de Serviço Inválido!\n"
    # Criando o Objeto de Manipulação das Reservas:
    reservationsManager = ReservationsManager(rl_contract)
    reservationsManager.getReservationsOnBlockchain(rl_contract)
    res_list = reservationsManager.reservationsList
    # Percorrendo as Reservas:
    for res in res_list:
        if str(res["customer"]) == str(customerAddress):
            try:
                # Marcando a Reserva Como Confirmada:
                print(f"Marcando Uma Reserva Como Confirmada: {int(res['reservationID'])}\n")
                tx_hash = rl_contract.functions.confirmReservation(int(res["reservationID"])).transact({
                    'from': server_account,
                    "nonce": w3.eth.get_transaction_count(server_account),
                    'gasPrice': w3.eth.gas_price,
                    "gas": 50000,
                    "chainId": w3.eth.chain_id
                })
                w3.eth.wait_for_transaction_receipt(tx_hash)
                # Verificando o Status da Reserva na Blockchain:
                rs = rl_contract.functions.getReservation(int(res["reservationID"])).call()
                rs_status = rs[10] # 0 = PENDING, 1 = CONFIRMED, 2 = PAYED, 3 = CANCELLED.
                if rs_status != 1:
                    print(f"Falha ao Marcar a Reserva '{int(res['reservationID'])}' Como Confirmada!\n")
                    return None

                # Criando o Escrow da Reserva:
                if res["companyName"] == "ecocharge":
                    recipient = company_accounts["ecocharge"]
                elif res["companyName"] == "eflux":
                    recipient = company_accounts["eflux"]
                elif res["companyName"] == "voltpoint":
                    recipient = company_accounts["voltpoint"]
                print(f"Criando o Escrow de Pagamento da Reserva: {int(res['reservationID'])}\n")
                tx_hash = escrow_contract.functions.initializeEscrow(int(res["reservationID"])).transact({
                    'from': server_account,
                    "nonce": w3.eth.get_transaction_count(server_account),
                    'gasPrice': w3.eth.gas_price,
                    "gas": 152000,
                    "chainId": w3.eth.chain_id
                })
                w3.eth.wait_for_transaction_receipt(tx_hash)
                # Comparando o Valor do Escrow de Pagamento Com o Valor da Reserva:
                escrow = escrow_contract.functions.getEscrowPaymentStatus(int(res["reservationID"])).call()
                escrow_amount = int(escrow[2])
                if escrow_amount != int(rs[7]):
                    print(f"Falha ao Criar o Escrow de Pagamento da Reserva '{int(res['reservationID'])}'!\n")
                    return None
            except Exception as e:
                print(f"Erro ao Marcar a Reserva '{int(res['reservationID'])}' Como Confirmada e Criar o Escrow de Pagamento: {e}\n")
    return True

# Marcando Todas as Reservas de Um Cliente Como Canceladas:
def markReservationsAsCanceled(w3: Web3, rl_contract, server_account, customerAddress):
    # Verificando os Dados:
    assert Web3.is_address(server_account), "Endereço da Conta do Prestador de Serviço Inválido!\n"
    # Criando o Objeto de Manipulação das Reservas:
    reservationsManager = ReservationsManager(rl_contract)
    reservationsManager.getReservationsOnBlockchain(rl_contract)
    res_list = reservationsManager.reservationsList
    # Percorrendo as Reservas:
    for res in res_list:
        if str(res["customer"]) == str(customerAddress):
            try:
                # Marcando a Reserva Como Cancelada:
                print(f"Marcando Uma Reserva Como Cancelada: {int(res['reservationID'])}\n")
                tx_hash = rl_contract.functions.cancelReservation(int(res["reservationID"])).transact({
                    'from': server_account,
                    "nonce": w3.eth.get_transaction_count(server_account),
                    'gasPrice': w3.eth.gas_price,
                    "gas": 50000,
                    "chainId": w3.eth.chain_id
                })
                w3.eth.wait_for_transaction_receipt(tx_hash)
                # Verificando o Status da Reserva na Blockchain:
                rs = rl_contract.functions.getReservation(int(res["reservationID"])).call()
                rs_status = rs[10] # 0 = PENDING, 1 = CONFIRMED, 2 = PAYED, 3 = CANCELLED.
                if rs_status != 3:
                    print(f"Falha ao Marcar a Reserva '{int(res['reservationID'])}' Como Cancelada!\n")
                    return None
            except Exception as e:
                print(f"Erro ao Marcar a Reserva '{int(res['reservationID'])}' Como Cancelada: {e}\n")
                return None
    return True
