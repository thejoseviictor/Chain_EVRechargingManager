# Inicializando a Blockchain Ganache e Seus Contratos -------------------------

# Importando as Dependências:
import os
from web3 import Web3
import time

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

    # Implantando o Contrato:
    ReservationLedger = w3.eth.contract(abi="app/contracts/", bytecode="app/contracts/")

    # Construindo a Transação de Implantação:
    transaction = ReservationLedger.constructor().build_transaction(
        {
            "from": owner_account,
            "nonce": w3.eth.get_transaction_count(owner_account),
            "gasPrice": w3.eth.gas_price,
        }
    )

    # Assinando a Transação:
    signed_transaction = w3.eth.account.sign_transaction(transaction, private_key=w3.eth.local_private_keys[0])

    # Enviando a Transação:
    tx_hash = w3.eth.send_raw_transaction(signed_transaction.rawTransaction)

    # Esperando Pela Mineração do Bloco e Obtendo o Recibo da Transação:
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    # Salvando o Endereço do Contrato:
    contract_address = tx_receipt.contract_address
    print(f"Contrato Implantado em: {contract_address}\n")

    # ENVIAR O ENDEREÇO DO CONTRATO PARA OS SERVIDORES VIA API!
