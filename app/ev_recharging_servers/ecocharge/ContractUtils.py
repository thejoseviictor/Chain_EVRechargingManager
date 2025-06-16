# Funções Úteis para Contratos Solidity ---------------------------------------------------------

# Importando as Dependências:
import os
from web3 import Web3
import json

# Caminho dos Contratos:
CONTRACTS_DIR = 'build/contracts/'

# Chave Privada do Deployer:
DEPLOYER_PRIVATE_KEY = os.environ.get('DEPLOYER_PRIVATE_KEY')

# Carregando o "ABI" de Um Contrato Compilado:
def getContractData(contract_name: str):
    with open(f"{CONTRACTS_DIR}{contract_name}.abi", 'r') as abi_file:
        abi = json.loads(abi_file.read()) # Lendo Como Dicionário.
    return abi

# Iniciando Uma Sessão de Carregamento:
def startChargingSession(w3: Web3, contract, server_account, reservationID: int):
    try:
        print(f"Iniciando a Sessão de Carregamento da Reserva: {reservationID}\n")
        tx_hash = contract.functions.startChargingSession(reservationID).transact({
            'from': server_account,
            "nonce": w3.eth.get_transaction_count(server_account),
            'gasPrice': w3.eth.gas_price,
            "gas": 3000000,
            "chainId": w3.eth.chain_id
        })
        w3.eth.wait_for_transaction_receipt(tx_hash)
        cs = contract.functions.getChargingSession(reservationID).call()
        cs_status = cs[1] # 0 = IDLE, 1 = IN_PROGRESS, 2 = FINISHED.
        if cs_status == 1:
            print(f"Sessão de Carregamento da Reserva '{reservationID}' Iniciada Com Sucesso!\n")
            return True
        else:
            print(f"Falha ao Iniciar a Sessão de Carregamento da Reserva '{reservationID}'!\n")
            return None
    except Exception as e:
        print(f"Erro ao Iniciar a Sessão de Carregamento da Reserva '{reservationID}': {e}\n")
        return None
