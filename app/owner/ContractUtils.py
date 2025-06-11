# Funções Úteis para Contratos Solidity ---------------------------------------------------------------------------

# Importando as Dependências:
from web3 import Web3

# Implementando um Contrato e Retornando o Seu Endereço:
def implementContract(w3: Web3, owner_account, abi: str, bytecode: str):
    # Verificando o Endereço da Conta do "Owner":
    if w3.is_checksum_address(owner_account):
        # Implantando o Contrato:
        Contract = w3.eth.contract(abi=abi, bytecode=bytecode)

        # Construindo a Transação de Implantação:
        transaction = Contract.constructor().build_transaction(
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

        # Retonando o Endereço do Contrato:
        return contract_address
