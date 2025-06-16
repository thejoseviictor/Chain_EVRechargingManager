# Funções Úteis para Contratos Solidity ---------------------------------------------------------

# Importando as Dependências:
import os
from web3 import Web3
import json
import time
import requests
from ReservationsManager import ReservationsManager

# Salvando as Informações do Owner:
OWNER_IP = os.environ.get(f'OWNER_IP')
OWNER_PORT = int(os.environ.get(f'OWNER_PORT'))

# Caminho dos Contratos:
CONTRACTS_DIR = 'build/contracts/'

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

# Recebendo os Endereços dos Contratos:
def getContractsAddresses():
    try:
        response = requests.get(f'http://{OWNER_IP}:{OWNER_PORT}/contracts')
        print(f"Endereços dos Contratos Recebidos Com Sucesso!\n")
        return response.json()
    # Tratando as Exceções:
    except Exception as e:
        print(f"Erro ao Receber os Endereços dos Contratos: {e}\n")
        return None

# Carregando o "ABI" e o "bytecode" de Um Contrato Compilado:
def getContractData(contract_name: str):
    with open(f"{CONTRACTS_DIR}{contract_name}.abi", 'r') as abi_file:
        abi = json.loads(abi_file.read()) # Lendo Como Dicionário.
    with open(f"{CONTRACTS_DIR}{contract_name}.bin", 'r') as bin_file:
        bytecode = bin_file.read() # Lendo Como String Hexadecimal.
    return abi, bytecode

# Criando uma Reserva "Pendente" na Blockchain:
def createReservationBlockchain(w3: Web3, contract, server_account, vehicleID: int, data: dict):
    # Recuperando os Arquivos Compilados:
    abi, bytecode = getContractData("ReservationLedger")

    # Implantando o Contrato:
    Contract = w3.eth.contract(abi=abi, bytecode=bytecode)
    try:
        # Verificando os Dados:
        assert isinstance(data["startTimestamp"], int)
        assert isinstance(data["finishTimestamp"], int)
        assert isinstance(data["chargingPointPower"], int)
        assert Web3.is_address(data["customerAddress"]), "Endereço inválido"
        # Enviando os Dados:
        print(f"Criando uma Reserva na Blockchain Para '{vehicleID}' em '{data["cityCodename"]}'\n")
        tx_hash = Contract.functions.createReservation(
            data["chargingStationID"],
            data["chargingPointID"],
            data["cityCodename"],
            data["companyName"],
            data["chargingPointPower"],
            data["kWhPrice"],
            data["startTimestamp"],
            data["finishTimestamp"],
            data["price"],
            data["customerAddress"]
        ).transact({
            'from': server_account,
            "nonce": w3.eth.get_transaction_count(server_account),
            'gasPrice': w3.eth.gas_price,
            "gas": 400000,
            "chainId": w3.eth.chain_id
        })
        w3.eth.wait_for_transaction_receipt(tx_hash)
    except Exception as e:
        print(f"Erro ao Criar Uma Reserva na Blockchain Para '{vehicleID}' em '{data["cityCodename"]}: {e}\n")
        return None

# Iniciando Uma Sessão de Carregamento:
def startChargingSession(w3: Web3, contract, server_account, reservationID: int):
    try:
        print(f"Iniciando a Sessão de Carregamento da Reserva: {reservationID}\n")
        tx_hash = contract.functions.startChargingSession(reservationID).transact({
            'from': server_account,
            "nonce": w3.eth.get_transaction_count(server_account),
            'gasPrice': w3.eth.gas_price,
            "gas": 65000,
            "chainId": w3.eth.chain_id
        })
        w3.eth.wait_for_transaction_receipt(tx_hash)
        cs = contract.functions.getChargingSession(reservationID).call()
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


# Marcando Todas as Reservas Pendentes de Um Usuário Como Confirmadas e Criando o Escrow:
def markReservationsAsConfirmed(w3: Web3, rl_contract, escrow_contract, server_account, customerAddress, company_accounts):
    # Criando o Objeto de Manipulação das Reservas:
    reservationsManager = ReservationsManager(rl_contract)
    reservationsManager.getReservationsOnBlockchain(rl_contract)
    res_list = reservationsManager.reservationsList
    # Percorrendo as Reservas:
    for res in res_list:
        if int(res["customer"]) == int(customerAddress):
            try:
                # Marcando a Reserva Como Confirmada:
                print(f"Marcando Uma Reserva Como Confirmada: {int(res['reservationID'])}\n")
                tx_hash = rl_contract.functions.confirmReservation(int(res["reservationID"])).transact({
                    'from': server_account,
                    "nonce": w3.eth.get_transaction_count(server_account),
                    'gasPrice': w3.eth.gas_price,
                    "gas": 52000,
                    "chainId": w3.eth.chain_id
                })
                w3.eth.wait_for_transaction_receipt(tx_hash)
                rs = rl_contract.functions.getReservation(int(res["reservationID"])).call()
                rs_status = rs[11] # 0 = PENDING, 1 = CONFIRMED, 2 = PAYED, 3 = CANCELLED.
                if rs_status != 1:
                    print(f"Falha ao Marcar a Reserva '{int(res['reservationID'])}' Como Confirmada!\n")

                # Criando o Escrow da Reserva:
                if res["companyName"] == "ecocharge":
                    recipient = company_accounts["ecocharge"]
                elif res["companyName"] == "eflux":
                    recipient = company_accounts["eflux"]
                elif res["companyName"] == "voltpoint":
                    recipient = company_accounts["voltpoint"]
                print(f"Criando o Escrow da Reserva: {int(res['reservationID'])}\n")
                tx_hash = escrow_contract.functions.initializeEscrow(
                    int(res["reservationID"]),
                    customerAddress,
                    recipient,
                    int(res["price"])
                ).transact({
                    'from': server_account,
                    "nonce": w3.eth.get_transaction_count(server_account),
                    'gasPrice': w3.eth.gas_price,
                    "gas": 200000,
                    "chainId": w3.eth.chain_id
                })
                w3.eth.wait_for_transaction_receipt(tx_hash)
            except Exception as e:
                print(f"Erro ao Marcar a Reserva '{int(res['reservationID'])}' Como Confirmada: {e}\n")

# Marcando Todas as Reservas de Um Cliente Como Canceladas:
def markReservationsAsCanceled(w3: Web3, rl_contract, server_account, customerAddress):
    # Criando o Objeto de Manipulação das Reservas:
    reservationsManager = ReservationsManager(rl_contract)
    reservationsManager.getReservationsOnBlockchain(rl_contract)
    res_list = reservationsManager.reservationsList
    # Percorrendo as Reservas:
    for res in res_list:
        if int(res["customer"]) == int(customerAddress):
            try:
                # Marcando a Reserva Como Cancelada:
                print(f"Marcando Uma Reserva Como Cancelada: {int(res['reservationID'])}\n")
                tx_hash = rl_contract.functions.cancelReservation(int(res["reservationID"])).transact({
                    'from': server_account,
                    "nonce": w3.eth.get_transaction_count(server_account),
                    'gasPrice': w3.eth.gas_price,
                    "gas": 52000,
                    "chainId": w3.eth.chain_id
                })
                w3.eth.wait_for_transaction_receipt(tx_hash)
                rs = rl_contract.functions.getReservation(int(res["reservationID"])).call()
                rs_status = rs[11] # 0 = PENDING, 1 = CONFIRMED, 2 = PAYED, 3 = CANCELLED.
                if rs_status != 3:
                    print(f"Falha ao Marcar a Reserva '{int(res['reservationID'])}' Como Cancelada!\n")
            except Exception as e:
                print(f"Erro ao Marcar a Reserva '{int(res['reservationID'])}' Como Cancelada: {e}\n")

# Marcando Uma Reserva Como Paga, Após Uma Transação:
def markReservationAsPayed(w3: Web3, contract, server_account, reservationID: int):
    try:
        print(f"Marcando Uma Reserva Como Paga: {reservationID}\n")
        tx_hash = contract.functions.markReservationAsPayed(reservationID).transact({
            'from': server_account,
            "nonce": w3.eth.get_transaction_count(server_account),
            'gasPrice': w3.eth.gas_price,
            "gas": 52000,
            "chainId": w3.eth.chain_id
        })
        w3.eth.wait_for_transaction_receipt(tx_hash)
        rs = contract.functions.getReservation(reservationID).call()
        rs_status = rs[11] # 0 = PENDING, 1 = CONFIRMED, 2 = PAYED, 3 = CANCELLED.
        if rs_status == 2:
            return True
        else:
            print(f"Falha ao Marcar a Reserva '{reservationID}' Como Paga!\n")
            return None
    except Exception as e:
        print(f"Erro ao Marcar a Reserva '{reservationID}' Como Paga: {e}\n")
        return None
