from dataclasses import dataclass

@dataclass
class User: # Informações básicas do próprietário do veículo

    cpf: str
    name: str
    email: str
    password: str
