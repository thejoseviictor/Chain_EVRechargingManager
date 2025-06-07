''' Classe responsável por manter métodos de definição de informações e simulações do veículo '''
from dataclasses import dataclass

import time
import os
import unicodedata # Biblioteca usada para tratar acentuações e caracteres

@dataclass
class VehicleUtility:


    @staticmethod
    def clearTerminal(): # Método utilizado para apagar terminal 
       os.system('cls' if os.name == 'nt' else 'clear')
    
    def endAnimation(self): # Método que cria uma pequena animação de encerramento de programa

        loadPoints = ["...", "..", ".", ""]

        for p in loadPoints:
            print(f"Encerando o programa {p} ")
            time.sleep(1)
            self.clearTerminal()
    
    def defineRoute(self, origin: str, destination: str): 
        
        '''
        Método responsável por determinar os codinomes das cidades de origem e de destino 
        baseado nas respostas do usuário

        '''
        route = []

        route.append(origin)
        route.append(destination)

        # Pega os valores determinados pelo usúario e substitui pelos codinomes correspondentes de cada cidade, também trata caso o usúario defina valores inválidos para a lógica
        for t in range( len(route) ) : 

            local = route[t]

            if local == "1":
                route[t] = "v_conquista"
                
            elif local == "2":
                route[t] = "jequie"
                
            elif local == "3":
                route[t] = "feira"
                
            elif local == "4":
                    route[t] = "e_cunha"

            elif local == "5":
                route[t] = "ibo"
                
            elif local == "6":
                route[t] = "barro"
                
            elif local == "7":
                route[t] = "jaguaribe"
                
            elif local == "8":
                route[t] = "russas"
                
            elif local == "9":
                route[t] = "fortaleza"
                
            else:
                route[t] = "false"
        
        if route[0] == "false" or route[1] == "false" :
            return False

        return route
    
    def writeReplyBack(self, wrongActions: bool, repeat: bool): # Método utilizado para voltar para o ínicio ou para encerrar o programa, dentro das opções de login(opções 1, 2, 3 e 4)

        reply = input("\n O que deseja agora: \n 1. Voltar para o início. \n 2. Fechar programa. \n ->")

        if reply == "1" :
            wrongActions = False
            repeat = True
            self.clearTerminal()

        else:
            wrongActions = False
            repeat = False
            self.endAnimation()

    def nomalizeName(self, fakeName: list[str]): # Método para normalizar(tratar) a representação de caracteres especiais(ç) ou acentuações(á, é, à, è, õ,ã, ê, ô, â ...) na geração de nomes aleatórios(str)

        genericName = []

        for n in fakeName:

            #Normalizando o primeiro nome e depois o sobrenome
            unormalizatedName = unicodedata.normalize('NFD', n) # Separação de caractere e acentuação
            normalizatedName = ''.join(c for c in unormalizatedName if not unicodedata.combining(c)) # Remoção das acentuações
            NameWithoutCedilhado = normalizatedName.replace('ç', 'c').replace('Ç', 'C') # Substituição dos caracteres "ç" e "Ç" por "c" e "C", respectivamente
            name = NameWithoutCedilhado.encode('ASCII', 'ignore').decode('ASCII') # Substituição de "ç" ou "Ç" por "c" e "Ç, respectivamente"

            genericName.append(name)

        return genericName
    
    def startAnimation(self): # Exibição inicial no programa

        title = "\t ------------- veHI : Sistema de recarga para veículos elétricos -------------\n"
        print(title)
        time.sleep(2)

