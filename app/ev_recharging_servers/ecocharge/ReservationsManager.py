from web3 import Web3
import datetime
from ChargingPointsFile import ChargingPointsFile

class Reservation:
    # Inicializando a Classe e seus Atributos:
    def __init__(self, chargingStationID: int, chargingPointID: int, cityCodename: str, companyName: str, chargingPointPower: float, kWhPrice: float,
                 actualBatteryPercentage: int, batteryCapacity: float, lastReservationFinishDateISO, timeToReach: float):
        self.chargingStationID = chargingStationID  # ID do Posto de Recarga.
        self.chargingPointID = chargingPointID  # ID do Ponto de Carregamento.
        self.cityCodename = cityCodename # Apelido da Cidade.
        self.companyName = companyName # Nome da Empresa.
        self.chargingPointPower = chargingPointPower # Potência do Ponto de Carregamento em kW.
        self.kWhPrice = kWhPrice    # Preço do kWh do Ponto de Carregamento.
        self.durationHours = self.calculateDuration(actualBatteryPercentage, batteryCapacity) # Duração da Recarga em Horas.
        self.timeToReach = timeToReach # Tempo Necessário, em Horas, Para o Veículo Alcançar Essa Reserva.
        # Formato ISO: 0000-00-00T00:00:00 (Ano, Mês, Dia, T(Separador Entre Data e Hora), Hora, Minutos, Segundos):
        self.startDateISO = self.calculateStartDateISO(lastReservationFinishDateISO)
        self.finishDateISO = self.calculateFinishDateISO()
        self.price = self.calculatePrice()  # Preço da Reserva.

    # Calculando o Preço da Reserva:
    # kWh = Potência do Carregador (kW) * Tempo (Horas)
    def calculatePrice(self):
        kWh = self.chargingPointPower * self.durationHours
        return kWh * self.kWhPrice

    # Calculando o Tempo para Completar a Carga de Bateria do Veículo:
    # Tempo (Horas) = Carga Necessária (kWh) / Potência do Carregador (kW)
    def calculateDuration(self, actualBatteryPercentage: int, batteryCapacity: float):
        # kWh Necessários = Capacidade Total (kWh) * ((100 - Porcentagem Atual) / 100):
        neededCharge = batteryCapacity * ((100 - actualBatteryPercentage) / 100) # Exemplo: Precisa de 80%, Então: Necessário = Capacidade Total * 0.80
        return (neededCharge / self.chargingPointPower)

    # Novas Reservas São Feitas para 5 Minutos Após a Última Reserva Cadastrada no Ponto de Carregamento:
    def calculateStartDateISO(self, lastReservationFinishDateISO):
        lastReservationFinishDateTime = datetime.datetime.fromisoformat(lastReservationFinishDateISO) # Decodificando para o Formato DateTime.
        resultedStartDateTime = lastReservationFinishDateTime + datetime.timedelta(hours=self.timeToReach) # Somando o Tempo para Alcançar.
        resultedStartDateTime += datetime.timedelta(minutes=5) # Somando Cinco Minutos.
        return resultedStartDateTime.isoformat() # Codificando Para o Formato ISO.
    
    # Calcula a Data Que o Veículo Irá Terminar de Usar o Ponto de Carregamento, de Acordo com a Duração da Recarga em Horas:
    # Data de Finalização = Data de Ínicio + Duração de Carregamento em Horas
    def calculateFinishDateISO(self):
        start = datetime.datetime.fromisoformat(self.startDateISO) # Decodificando a Data de Ínicio do Formato ISO para DateTime.
        finish = start + datetime.timedelta(hours=self.durationHours) # Calculando a Data de Finalização.
        return finish.isoformat() # Codificando a Data de Finalização do DateTime para Formato ISO.

# Manipulação de Dados das Reservas:
class ReservationsManager:
    def __init__(self, rl_contract):
        self.rl_contract = rl_contract # Contrato "ReservationLedger".
        self.reservationsList = [] # Lista de Reservas.
    
    # Recuperando as Reservas Salvas na Blockchain:
    def getReservationsOnBlockchain(self, rl_contract):
        reservations = rl_contract.functions.getAllReservations().call()
        # Convertendo a Tupla de Reservas para Dicionário:
        for res in reservations:
            res_dict = {
                "reservationID": res[0],
                "chargingStationID": res[1],
                "chargingPointID": res[2],
                "cityCodename": res[3],
                "companyName": res[4],
                "startTimestamp": datetime.datetime.fromtimestamp(res[5]).isoformat(),
                "finishTimestamp": datetime.datetime.fromtimestamp(res[6]).isoformat(),
                "price": res[7],
                "customer": res[8],
                "recipient": res[9],
                "status": res[10]
            }
            self.reservationsList.append(res_dict)
        # Exibindo Mensagem de Sucesso:
        print(f"{len(self.reservationsList)} Reservas Recuperadas da Blockchain Para Memória de Trabalho.\n")

    # Listando Todas as Reservas Cadastradas para os Pontos de Carregamento, em um Posto de Recarga Específico:
    def listReservations(self, chargingStationID: int):
        self.getReservationsOnBlockchain(self.rl_contract) # Recuperando os Dados da Blockchain.
        searchList = [] # Onde Serão Salvas as Reservas Encontradas.
        for reservation in self.reservationsList:
            if reservation["chargingStationID"] == chargingStationID:
                searchList.append(reservation)
        return searchList # Retornando as Reservas Encontradas.

    # Encontrando a Data de Finalização da Última Reserva Cadastrada em um Ponto de Carregamento Específico:
    # Resumindo, Descobrir Quando o Último Veículo Vai Terminar de Usar o Ponto de Carregamento.
    def getLastReservationFinishDateISO(self, chargingStationID: int, chargingPointID: int):
        self.getReservationsOnBlockchain(self.rl_contract) # Recuperando os Dados da Blockchain.
        found = False # Indicará Se um Data Posterior For Encontrada.
        lastDateTime = datetime.datetime(1999, 12, 31, 0, 0, 0) # Data de Base para Comparação Inicial.
        # Percorrendo a Lista de Reservas:
        for reservation in self.reservationsList:
            if reservation["chargingStationID"] == chargingStationID and reservation["chargingPointID"] == chargingPointID :
                dateTimeInFile = datetime.datetime.fromisoformat(reservation["finishDateISO"]) # Decodificando a Data na Lista para DateTime.
                # Salvando, Se a Data na Lista For Posterior:
                if lastDateTime < dateTimeInFile:
                    found = True # Alterando o Status de Data Posterior Encontrada.
                    lastDateTime = dateTimeInFile 
        if found:
            return lastDateTime.isoformat() # Retornando a Data Encontrada Codificada em ISO.
        # Retorna "None", Se Não Houver Nenhuma Reserva no Ponto de Carregamento:
        else:
            return None
    
    # Retornando um Dicionário Com a Estrutura da Reserva Formatado Para Envio Para Blockchain:
    def createReservation(self, chargingStationID: int, chargingPointID: int, cityCodename: str, companyName: str,
                          actualBatteryPercentage: int, batteryCapacity: float, timeToReach: float, customerAddress):
        self.getReservationsOnBlockchain(self.rl_contract) # Recuperando os Dados da Blockchain.
        # Buscando Informações do Ponto de Carregamento Selecionado:
        cp = ChargingPointsFile() # cp = Charging Point.
        cp = cp.findChargingPoint(chargingPointID, chargingStationID) # Salvando a Celula Encontrada.
        if cp:
            chargingPointPower = cp["power"]
            kWhPrice = cp["kWhPrice"]
            # Descobrindo a Data de Finalização da Última Reserva:
            lastReservationFinishDateISO = self.getLastReservationFinishDateISO(chargingStationID, chargingPointID)
            # Se Não Houverem Reservas, a Nova Reserva Será do Horário Atual + 5 Minutos:
            if lastReservationFinishDateISO is None:
                lastReservationFinishDateISO = datetime.datetime.now().isoformat()
            # Gerando o Objeto da Reserva:
            reservationObj = Reservation(chargingStationID, chargingPointID, cityCodename, companyName, chargingPointPower, kWhPrice,
                                         actualBatteryPercentage, batteryCapacity, lastReservationFinishDateISO, timeToReach)
            # Estruturando a Reserva:
            createdReservation = ({
                "chargingStationID": int(reservationObj.chargingStationID),
                "chargingPointID": int(reservationObj.chargingPointID),
                "cityCodename": str(reservationObj.cityCodename),
                "companyName": str(reservationObj.companyName),
                "durationHours": reservationObj.durationHours,
                "startTimestamp": int(datetime.datetime.fromisoformat(reservationObj.startDateISO).timestamp()),
                "finishTimestamp": int(datetime.datetime.fromisoformat(reservationObj.finishDateISO).timestamp()),
                "price": int(Web3.to_wei(reservationObj.price, 'ether')),
                "customerAddress": str(customerAddress)
            })
            
            return createdReservation # Retornando a Estrutura da Reserva Formatada.
        else:
            print(f'Ponto de Carregamento com ID {chargingPointID}, no Posto de Recarga com ID {chargingStationID}, Não Foi Encontrado!\n')
            return None
