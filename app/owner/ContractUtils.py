# Funções Úteis para Contratos Solidity ---------------------------------------------------------------------------

# Importando as Dependências:
import os
from web3 import Web3
import json

# Caminho dos Contratos:
CONTRACTS_DIR = 'build/contracts/'

# Chave Privada do Deployer:
DEPLOYER_PRIVATE_KEY = os.environ.get('DEPLOYER_PRIVATE_KEY')

# Carregando o "ABI" e o "bytecode" de Um Contrato Compilado:
def getContractData(contract_name: str):
    with open(f"{CONTRACTS_DIR}{contract_name}.abi", 'r') as abi_file:
        abi = json.loads(abi_file.read()) # Lendo Como Dicionário.
    with open(f"{CONTRACTS_DIR}{contract_name}.bin", 'r') as bin_file:
        bytecode = bin_file.read() # Lendo Como String Hexadecimal.
    return abi, bytecode

# Implementando um Contrato e Retornando o Seu Endereço:
def deployContract(w3: Web3, deployer_account, contract_name: str, *args):
    # Recuperando os Arquivos Compilados:
    abi, bytecode = getContractData(contract_name)

    # Implantando o Contrato:
    Contract = w3.eth.contract(abi=abi, bytecode=bytecode)

    # Construindo a Transação de Deploy:
    transaction = Contract.constructor(*args).build_transaction({
            "from": deployer_account,
            "nonce": w3.eth.get_transaction_count(deployer_account),
            "gasPrice": w3.eth.gas_price,
            "gas": 3000000,
            "chainId": w3.eth.chain_id,
    })
    
    # Assinando a Transação:
    signed_tx = w3.eth.account.sign_transaction(transaction, private_key=DEPLOYER_PRIVATE_KEY)

    # Enviando a Transação:
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    print(f"Hash da Transação de Deploy de '{contract_name}': {tx_hash.hex()}\n")

    # Esperando Pela Mineração do Bloco e Obtendo o Recibo da Transação:
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    # Salvando o Endereço do Contrato:
    contract_address = tx_receipt.contractAddress
    print(f"Contrato '{contract_name}' Deployado em: {contract_address}\n")

    # Retonando o Contrato e Endereço:
    return w3.eth.contract(address=contract_address, abi=abi)

# Autorizando o Servidor de Uma Empresa na Blockchain:
def authorizeServer(w3: Web3, contract, deployer_account, server_account):
    try:
        print(f"Autorizando o Servidor: {server_account}\n")
        tx_hash = contract.functions.authorizeRechargingServer(server_account).transact({
            'from': deployer_account,
            "nonce": w3.eth.get_transaction_count(deployer_account),
            'gasPrice': w3.eth.gas_price,
            "gas": 3000000,
            "chainId": w3.eth.chain_id
        })
        w3.eth.wait_for_transaction_receipt(tx_hash)
        is_auth = contract.functions.isAuthorizedRechargingServer(server_account).call()
        print(f"Estado da Autorização do Servidor '{server_account}': {is_auth}\n")
    except Exception as e:
        print(f"Erro ao Autorizar o Servidor '{server_account}': '{e}'\n")

# Finalizando Uma Sessão de Carregamento e Liberando os Fundos de Pagamento:
def finishChargingSession(w3: Web3, contract, deployer_account, reservationID: int):
    try:
        print(f"Finalizando a Sessão de Carregamento da Reserva: {reservationID}\n")
        tx_hash = contract.functions.finishChargingSession(reservationID).transact({
            'from': deployer_account,
            "nonce": w3.eth.get_transaction_count(deployer_account),
            'gasPrice': w3.eth.gas_price,
            "gas": 3000000,
            "chainId": w3.eth.chain_id
        })
        w3.eth.wait_for_transaction_receipt(tx_hash)
        cs = contract.functions.getChargingSession(reservationID).call()
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
