// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract ReservationLedger {
    enum public Status {PENDING, CONFIRMED, COMPLETED, PAYED, CANCELLED}

    // Dados da Reserva:
    struct Reservation {
        uint256 reservationID;
        uint256 chargingStationID;
        uint256 chargingPointID;
        string cityName;
        string cityCodename;
        string companyName;
        uint256 chargingPointPower;
        uint256 kWhPrice; // Em "wei", Menor Unidade de Valor do Ethereum.
        uint256 vehicleID;
        uint256 startDateTime; // Converter ISO para "timestamp".
        uint256 finishDateTime;
        uint256 durationHours; // Duração em Horas.
        uint256 estimatedPrice; // Preço Estimado em "wei".
        address payable customer; // Endereço da Carteira do Cliente, Para Pagamentos.
        Status status;
        Status paymentStatus;
    }

    // Dados da Transação:
    struct TransactionRecord {
        uint256 transactionID;
        uint256 reservationID;
        uint256 actualKWhConsumed; // kWh Consumidos Realmente.
        uint256 finalPrice; // Preço Final da Transação em "wei".
        address payer; // Endereço da Carteira que Efetuou o Pagamento.
        bool paid; // Indica Se o Pagamento foi Confirmado.
        uint256 transactionTimestamp;
    }

    // Mapeamentos:
    mapping(uint256 => Reservation) public reservations;
    mapping(uint256 => TransactionRecord) public transactionRecords;

    // Contadores de IDs:
    uint256 public nextReservationID;
    uint256 public nextTransactionID;

    // Eventos para Notificações:
    event ReservationCreated(
        uint256 indexed reservationID,
        uint256 indexed chargingStationID,
        uint256 indexed chargingPointID,
        address indexed customer,
        uint256 startDateTime,
        uint256 estimatedPrice
    );
    event ReservationStatusUpdated(uint256 indexed reservationID, Status status);
    event TransactionRecorded(
        uint256 indexed transactionID,
        uint256 indexed reservationID,
        uint256 finalPrice,
        address indexed payer,
        uint256 actualKWhConsumed
    );

    // Apenas o Cliente (customer) Pode Modificar/Cancelar Sua Própria Reserva:
    modifier onlyCustomer(uint256 _reservationID) {
        require(reservations[_reservationID].customer == msg.sender, "Apenas o Cliente Pode Executar Esta Ação!");
        _;
    }

    // Construtor:
    constructor() {
        nextReservationID = 1;
        nextTransactionID = 1;
    }

    // Criando uma Nova Reserva:
    function createReservation(
        uint256 memory _chargingStationID,
        uint256 memory _chargingPointID,
        string memory _cityName,
        string memory _cityCodename,
        string memory _companyName,
        uint256 memory _chargingPointPower,
        uint256 memory _kWhPrice,
        uint256 memory _vehicleID,
        uint256 memory _startDateTime,
        uint256 memory _finishDateTime,
        uint256 memory _durationHours,
        address _customerAddress // Endereço da Carteira do Cliente.
    ) public returns (uint256) {
        // Calculando o Preço Estimado: Potência do Carregador * Duração Estimada em Horas * Preço kWh do Carregador
        uint256 estimatedPrice = _chargingPointPower * _durationHours * _kWhPrice;

        // Criando a Reserva:
        uint256 newReservationID = nextReservationID;
        reservations[newReservationID] = Reservation({
            reservationID: newReservationID,
            chargingStationID: _chargingStationID,
            chargingPointID: _chargingPointID,
            cityName: _cityName,
            cityCodename: _cityCodename,
            companyName: _companyName,
            chargingPointPower: _chargingPointPower,
            kWhPrice: _kWhPrice,
            vehicleID: _vehicleID,
            startDateTime: _startDateTime,
            finishDateTime: _finishDateTime,
            durationHours: _durationHours,
            estimatedPrice: estimatedPrice,
            customer: payable(_customerAddress),
            status: CONFIRMED,
            paymentStatus: PENDING
        });

        // Incrementando o ID Para a Próxima Reserva:
        nextReservationID++;

        // Emitindo a Notificação:
        emit ReservationCreated(
            newReservationID,
            _chargingStationID,
            _chargingPointID,
            _customerAddress,
            _startDateTime,
            estimatedPrice
        );

        // Retornando o ID da Reserva:
        return newReservationID;
    }

    // Cancelando uma Reserva Existente:
    function cancelReservation(uint256 _reservationID) public onlyCustomer(_reservationID) {
        // Verificando o Estado da Reserva:
        require(reservations[_reservationID].reservationID != 0, "ID da Reserva Inválido!");
        require(reservations[_reservationID].status != CANCELLED, "A Reserva Já Estava Cancelada!");
        require(reservations[_reservationID].status == CONFIRMED, "A Reserva Já Foi Executada e Finalizada!");
        require(block.timestamp < reservations[_reservationID].startDateTime, "Não é Possível Cancelar uma Reserva Já Iniciada!");

        // Atualizando o Status da Reserva:
        reservations[_reservationID].status = CANCELLED;

        // Emitindo a Notificação:
        emit ReservationStatusUpdated(_reservationID, reservations[_reservationID].status);
    }

    // Marcando uma Reserva como Concluída:
    function completeReservation(uint256 _reservationID) public onlyCustomer(_reservationID) {
        // Verificando o Estado da Reserva:
        require(reservations[_reservationID].reservationID != 0, "ID da Reserva Inválido!");
        require(reservations[_reservationID].status != CANCELLED, "A Reserva Está Cancelada!");
        require(reservations[_reservationID].status == CONFIRMED, "A Reserva Já Foi Executada e Finalizada!");
        require(block.timestamp > reservations[_reservationID].startDateTime, "A Reserva Ainda Não Foi Iniciada!");

        // Atualizando o Status da Reserva:
        reservations[_reservationID].status = COMPLETED;

        // Emitindo a Notificação:
        emit ReservationStatusUpdated(_reservationID, reservations[_reservationID].status);
    }

}