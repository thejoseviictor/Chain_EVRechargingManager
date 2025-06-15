# Funções Úteis para Contratos Solidity ---------------------------------------------------------------------------

# Importando as Dependências:
from web3 import Web3
import json

# Caminho dos Contratos:
CONTRACTS_DIR = 'build/contracts/'

# Carregando o "ABI" e o "bytecode" de Um Contrato Compilado:
def getContractData(contract_name: str):
    with open(f"{CONTRACTS_DIR}{contract_name}.abi", 'r') as abi_file:
        abi = json.loads(abi_file.read()) # Lendo Como Dicionário.
    with open(f"{CONTRACTS_DIR}{contract_name}.bin", 'r') as bin_file:
        bytecode = bin_file.read() # Lendo Como String Hexadecimal.
    return abi, bytecode

# Implementando um Contrato e Retornando o Seu Endereço:
# Todas as Contas São Locais e Desbloqueadas no Ganache, Não Sendo Necessário Assinar as Transações.
def deployContract(w3: Web3, deployer_account, contract_name: str, *args):
    # Verificando o Endereço da Conta do Deployer:
    if w3.is_checksum_address(deployer_account):
        # Recuperando os Arquivos Compilados:
        abi, bytecode = getContractData(contract_name)

        # Implantando o Contrato:
        Contract = w3.eth.contract(abi=abi, bytecode=bytecode)

        # Construindo a Transação de Deploy:
        transaction = Contract.constructor(*args).build_transaction(
            {
                "from": deployer_account,
                "nonce": w3.eth.get_transaction_count(deployer_account),
                "gasPrice": w3.eth.gas_price,
            }
        )

        # Enviando a Transação:
        tx_hash = w3.eth.send_transaction(transaction)
        print(f"Hash da Transação de Deploy de '{contract_name}': {tx_hash.hex()}\n")

        # Esperando Pela Mineração do Bloco e Obtendo o Recibo da Transação:
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

        # Salvando o Endereço do Contrato:
        contract_address = tx_receipt.contract_address
        print(f"Contrato '{contract_name}' Deployado em: {contract_address}\n")

        # Retonando o Contrato e Endereço:
        return w3.eth.contract(address=contract_address, abi=abi)
    return None

def authorizeServer(w3: Web3, contract, deployer_account, server_account):
    # Verificando o Endereço da Conta do Deployer e Servidor:
    if w3.is_checksum_address(deployer_account) and w3.is_checksum_address(server_account):
        try:
            print(f"Autorizando o Servidor: {server_account}\n")
            
            tx_hash = contract.functions.authorizeRechargingServer(server_account).transact({
                'from': deployer_account,
                "nonce": w3.eth.get_transaction_count(deployer_account),
                'gasPrice': w3.eth.gas_price
            })

            w3.eth.wait_for_transaction_receipt(tx_hash)

            is_auth = contract.functions.isAuthorizedRechargingServer(server_account).call()
            print(f"Estado da Autorização do Servidor '{server_account}': {is_auth}\n")
        except Exception as e:
            print(f"Erro ao Autorizar o Servidor '{server_account}': '{e}'\n")
