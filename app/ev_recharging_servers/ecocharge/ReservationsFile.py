# Será Armazenada no Arquivo de Reservas do Postos de Recarga:

import json
import os
import datetime
from ChargingPointsFile import ChargingPointsFile

class Reservation:
    # Inicializando a Classe e seus Atributos:
    def __init__(self, reservationID: int, chargingStationID: int, chargingPointID: int, cityName: str, cityCodename: str, companyName: str, chargingPointPower: float,
                 kWhPrice: float, vehicleID: int, actualBatteryPercentage: int, batteryCapacity: float, lastReservationFinishDateTime, timeToReach: float):
        self.reservationID = reservationID    # ID da Reserva.
        self.chargingStationID = chargingStationID  # ID do Posto de Recarga.
        self.chargingPointID = chargingPointID  # ID do Ponto de Carregamento.
        self.cityName = cityName # Nome da Cidade.
        self.cityCodename = cityCodename # Apelido da Cidade.
        self.companyName = companyName # Nome da Empresa.
        self.chargingPointPower = chargingPointPower # Potência do Ponto de Carregamento em Watt.
        self.kWhPrice = kWhPrice    # Preço do kWh do Ponto de Carregamento.
        self.vehicleID = vehicleID  # ID do Veículo.
        self.duration = self.calculateDuration(actualBatteryPercentage, batteryCapacity) # Duração da Recarga em Horas.
        self.timeToReach = timeToReach # Tempo Necessário, em Horas, Para o Veículo Alcançar Essa Reserva.
        self.startDateTime = self.calculateStartDateTime(lastReservationFinishDateTime) # Formato ISO: 0000-00-00T00:00:00 (Ano, Mês, Dia, T(Separador Entre Data e Hora), Hora, Minutos, Segundos)
        self.finishDateTime = self.calculateFinishDateTime() # Formato ISO: 0000-00-00T00:00:00 (Ano, Mês, Dia, T(Separador Entre Data e Hora), Hora, Minutos, Segundos)
        self.price = self.calculatePrice()  # Preço da Recarga.

    # Calculando o Preço da Recarga:
    # kWh = Potência do Carregador (kW) * Tempo (Horas)
    def calculatePrice(self):
        kWh = self.chargingPointPower * self.duration
        return kWh * self.kWhPrice

    # Calculando o Tempo para Completar a Carga de Bateria do Veículo:
    # Tempo (Horas) = Carga Necessária (kWh) / Potência do Carregador (kW)
    def calculateDuration(self, actualBatteryPercentage: int, batteryCapacity: float):
        # kWh Necessários = Capacidade Total (kWh) * ((100 - Porcentagem Atual) / 100):
        neededCharge = batteryCapacity * ((100 - actualBatteryPercentage) / 100) # Exemplo: Precisa de 80%, Então: Necessário = Capacidade Total * 0.80
        return (neededCharge / self.chargingPointPower)

    # Novas Reservas São Feitas para 5 Minutos Após a Última Reserva Cadastrada no Ponto de Carregamento:
    def calculateStartDateTime(self, lastReservationFinishDateTime):
        lastReservationFinishDateTime = datetime.datetime.fromisoformat(lastReservationFinishDateTime) # Decodificando para o Formato DateTime.
        resultedStartDateTime = lastReservationFinishDateTime + datetime.timedelta(hours=self.timeToReach) # Somando o Tempo para Alcançar.
        resultedStartDateTime += datetime.timedelta(minutes=5) # Somando Cinco Minutos.
        return resultedStartDateTime.isoformat() # Codificando Para o Formato ISO.
    
    # Calcula a Data Que o Veículo Irá Terminar de Usar o Ponto de Carregamento, de Acordo com a Duração da Recarga em Horas:
    # Data de Finalização = Data de Ínicio + Duração de Carregamento em Horas
    def calculateFinishDateTime(self):
        start = datetime.datetime.fromisoformat(self.startDateTime) # Decodificando a Data de Ínicio do Formato ISO para DateTime.
        finish = start + datetime.timedelta(hours=self.duration) # Calculando a Data de Finalização.
        return finish.isoformat() # Codificando a Data de Finalização do DateTime para Formato ISO.

# Salvando as Reservas em um Arquivo ".json":
class ReservationsFile: 
    # Inicializando a Classe e seus Atributos:
    def __init__(self, json_file="reservations.json"):
        os.makedirs("data", exist_ok=True) # Criando a Pasta "data", Se Não Existir.
        self.json_file = os.path.join("data", json_file) # Salvando o Banco de Dados na Pasta "data".
        self.reservationsList = [] # Lista de Reservas.
        self.readReservations() # Recuperando os Dados do Arquivo ".json"
    
    # Lendo as Reservas no Arquivo ".json":
    def readReservations(self):
        if os.path.exists(self.json_file):
            try:
                with open(self.json_file, "r", encoding="utf-8") as file:
                    self.reservationsList = json.load(file) # Salvando os Dados na Lista.
            except json.JSONDecodeError:
                print(f"Arquivo '{self.json_file}' Está Inválido ou Vazio!\n")
    
    # Verificando Se o Veículo Tem Reserva em um Posto de Recarga Específico:
    def findReservation(self, chargingStationID: int, vehicleID: int):
        self.readReservations() # Atualizando a Memória de Execução Com o Banco de Dados em "reservations.json".
        for reservation in self.reservationsList:
            if reservation["chargingStationID"] == chargingStationID and reservation["vehicleID"] == vehicleID:
                return reservation
        print(f"Nenhuma Reserva Foi Encontrada Para o Veículo com ID '{vehicleID}' no Posto de Recarga '{chargingStationID}'!\n")
        return None

    # Listando Todas as Reservas Cadastradas para os Pontos de Carregamento, em um Posto de Recarga Específico:
    def listReservations(self, chargingStationID: int):
        searchList = [] # Onde Serão Salvas as Reservas Encontradas.
        for reservation in self.reservationsList:
            if reservation["chargingStationID"] == chargingStationID:
                searchList.append(reservation)
        return searchList # Retornando as Reservas Encontradas.

    # Salvando a Lista de Reservas no Arquivo ".json":
    def saveReservations(self):
        with open(self.json_file, "w", encoding="utf-8") as file:
            json.dump(self.reservationsList, file, indent=4, ensure_ascii=False)

    # Encontrando a Data de Finalização da Última Reserva Cadastrada em um Ponto de Carregamento Específico:
    # Resumindo, Descobrir Quando o Último Veículo Vai Terminar de Usar o Ponto de Carregamento.
    def getLastReservationFinishDateTime(self, chargingStationID: int, chargingPointID: int):
        self.readReservations() # Atualizando a Memória de Execução Com o Banco de Dados em "reservations.json".
        found = False # Indicará Se um Data Posterior For Encontrada.
        lastDateTime = datetime.datetime(1999, 12, 31, 0, 0, 0) # Data de Base para Comparação Inicial.
        # Percorrendo a Lista de Reservas:
        for reservation in self.reservationsList:
            if reservation["chargingStationID"] == chargingStationID and reservation["chargingPointID"] == chargingPointID :
                dateTimeInFile = datetime.datetime.fromisoformat(reservation["finishDateTime"]) # Decodificando a Data na Lista para DateTime.
                # Salvando, Se a Data na Lista For Posterior:
                if lastDateTime < dateTimeInFile:
                    found = True # Alterando o Status de Data Posterior Encontrada.
                    lastDateTime = dateTimeInFile 
        if found:
            return lastDateTime.isoformat() # Retornando a Data Encontrada Codificada em ISO.
        # Retorna "None", Se Não Houver Nenhuma Reserva no Ponto de Carregamento:
        else:
            return None
    
    # Gerando um ID para Nova Reserva:
    # Os IDs Não Podem Ser Iguais Para o Mesmo Servidor.
    # IDs Novos: Maior ID + 1.
    def generateReservationID(self):
        startID = 1 # Um ID Inicial Que Será Usado Como Comparador.
        for reservation in self.reservationsList:
            # ID Maior ou Igual (Para o Primeiro ID das Reservas):
            if reservation["reservationID"] >= startID:
                startID = reservation["reservationID"] + 1
        return startID
    
    # Criando uma Reserva e Salvando no Arquivo ".json":
    def createReservation(self, chargingStationID: int, chargingPointID: int, cityName: str, cityCodename: str, companyName: str,
                          vehicleID: int, actualBatteryPercentage: int, batteryCapacity: float, timeToReach: float):
        self.readReservations() # Atualizando a Memória de Execução Com o Banco de Dados em "reservations.json".
        # Verificando Se o Veículo Já Tem uma Reserva Neste Posto de Recarga:
        oldReservation = self.findReservation(chargingStationID, vehicleID)
        if oldReservation:
            return oldReservation # Retornando a Reserva Existente.
        # Buscando Informações do Ponto de Carregamento Selecionado:
        cp = ChargingPointsFile() # cp = Charging Point.
        cp = cp.findChargingPoint(chargingPointID, chargingStationID) # Salvando a Celular Encontrada.
        if cp:
            chargingPointPower = cp["power"]
            kWhPrice = cp["kWhPrice"]
            # Gerando o ID da Nova Reserva:
            reservationID = self.generateReservationID()
            # Descobrindo a Data de Finalização da Última Reserva:
            lastReservationFinishDateTime = self.getLastReservationFinishDateTime(chargingStationID, chargingPointID)
            # Se Não Houverem Reservas, a Nova Reserva Será do Horário Atual + 5 Minutos:
            if lastReservationFinishDateTime is None:
                lastReservationFinishDateTime = datetime.datetime.now().isoformat()
            # Gerando o Objeto da Reserva:
            reservationObj = Reservation(reservationID, chargingStationID, chargingPointID, cityName, cityCodename, companyName, chargingPointPower,
                                         kWhPrice, vehicleID, actualBatteryPercentage, batteryCapacity, lastReservationFinishDateTime, timeToReach)
            # Salvando as Informações da Reserva na Lista:
            createdReservation = ({
                "reservationID": reservationObj.reservationID, 
                "chargingStationID": reservationObj.chargingStationID, 
                "chargingPointID": reservationObj.chargingPointID, 
                "cityName": reservationObj.cityName, 
                "cityCodename": reservationObj.cityCodename, 
                "companyName": reservationObj.companyName, 
                "chargingPointPower": reservationObj.chargingPointPower, 
                "kWhPrice": reservationObj.kWhPrice, 
                "vehicleID": reservationObj.vehicleID, 
                "startDateTime": reservationObj.startDateTime,
                "finishDateTime": reservationObj.finishDateTime, 
                "duration": reservationObj.duration, 
                "price": reservationObj.price})
            self.reservationsList.append(createdReservation)
            self.saveReservations() # Salvando no Arquivo .json.
            print(f"Reserva para Veículo com ID '{vehicleID}' Foi Criada com Sucesso!\n")
            return createdReservation # Retornando a Reserva Criada.
        else:
            print(f'Ponto de Carregamento com ID {chargingPointID}, no Posto de Recarga com ID {chargingStationID}, Não Foi Encontrado!\n')
            return None
    
    # Removendo uma Reserva de um Veículo Específico:
    def deleteReservation(self, reservationID: int, chargingStationID: int, chargingPointID: int, vehicleID: int):
        self.readReservations() # Atualizando a Memória de Execução.
        for reservation in self.reservationsList:
            if reservation["reservationID"] == reservationID and reservation["vehicleID"] == vehicleID:
                if reservation["chargingStationID"] == chargingStationID and reservation["chargingPointID"] == chargingPointID:
                    self.reservationsList.remove(reservation)
                    self.saveReservations() # Salvando no Arquivo ".json".
                    print(f"A Reserva Com ID '{reservationID}' Foi Removida com Sucesso!\n")
                    return True
        print(f"A Reserva Com ID '{reservationID}' Não Foi Encontrada!\n")
        return None
