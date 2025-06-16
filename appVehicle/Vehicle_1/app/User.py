from dataclasses import dataclass

@dataclass
class User: # Informações básicas do próprietário do veículo

    def __init__(self, cpf: str, name: str, email: str, password: str) :

       self.cpf = cpf
       self.name = name
       self.email = email
       self.password = password
