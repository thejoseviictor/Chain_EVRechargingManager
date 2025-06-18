// SPDX-License-Identifier: MIT
pragma solidity 0.8.0;

// Importando as Dependências dos Outros Contratos:
import "./AuthorizedServers.sol";

contract ReservationLedger {
    // O Deployer do Contrato, Administrador:
    address public owner;

    // Referência ao Contrato "AuthorizedServers":
    AuthorizedServers public authorizedServers;

    // Status da Reserva:
    enum Status {PENDING, CONFIRMED, PAYED, CANCELLED}

    // Dados da Reserva:
    struct Reservation {
        uint16 reservationID; // 65536 IDs Possíveis, Para Economizar Recursos.
        uint8 chargingStationID; // 256 IDs Possíveis, Para Economizar Recursos.
        uint8 chargingPointID; // 256 IDs Possíveis, Para Economizar Recursos.
        string cityCodename;
        string companyName;
        uint32 startTimestamp;
        uint32 finishTimestamp;
        uint72 price; // Preço em "wei", Até "100" ETH em wei (1e20).
        address payable customer; // Endereço da Carteira do Cliente, Para Pagamentos.
        address payable recipient; // Endereço da Carteira do Servidor da Empresa do Posto.
        Status status;
    }

    // Mapeamentos:
    mapping(uint16 => Reservation) public reservations; // Até 65536 Reservas Possíveis.
    mapping(address => uint16[]) private customerReservationIDs;  // Até 65 Reservas Por Cliente Possíveis, Para 1000 Clientes.

    // Contadores de IDs:
    uint16 public nextReservationID;

    // Eventos para Notificações:
    event ReservationCreated(
        uint16 indexed reservationID,
        address customer,
        address recipient,
        string cityCodename,
        uint72 price
    );
    event ReservationStatusUpdated(uint16 indexed reservationID, Status status);

    // Modificador:
    modifier onlyServerOrOwner() {
        require(authorizedServers.isAuthorizedRechargingServer(msg.sender) || msg.sender == owner, "Apenas um Dos Servidores de Carregamento ou Administrador Pode Executar Esta Acao!");
        _;
    }

    // Construtor:
    constructor(address _authorizedServersAddress) {
        owner = msg.sender; // Define o Deployer do Contrato Como o Owner.
        authorizedServers = AuthorizedServers(_authorizedServersAddress);
        nextReservationID = 1;
    }

    // Criando uma Nova Reserva:
    function createReservation(
        uint8 _chargingStationID,
        uint8 _chargingPointID,
        string memory _cityCodename,
        string memory _companyName,
        uint32 _startTimestamp,
        uint32 _finishTimestamp,
        uint72 _price,
        address _customerAddress, // Endereço da Carteira do Cliente.
        address _companyAddress // Endereço da Carteira do Servidor da Empresa.
    ) public onlyServerOrOwner {
        // Criando a Reserva:
        uint16 newReservationID = nextReservationID;
        reservations[newReservationID] = Reservation({
            reservationID: newReservationID,
            chargingStationID: _chargingStationID,
            chargingPointID: _chargingPointID,
            cityCodename: _cityCodename,
            companyName: _companyName,
            startTimestamp: _startTimestamp,
            finishTimestamp: _finishTimestamp,
            price: _price,
            customer: payable(_customerAddress),
            recipient: payable(_companyAddress),
            status: Status.PENDING
        });

        // Associando o ID da Reserva ao Endereço da Carteira do Cliente:
        customerReservationIDs[_customerAddress].push(newReservationID);

        // Incrementando o ID Para a Próxima Reserva:
        nextReservationID++;

        // Emitindo a Notificação:
        emit ReservationCreated(
            newReservationID,
            _customerAddress,
            _companyAddress,
            _cityCodename,
            _price
        );
    }

    // Confirmando uma Reserva:
    function confirmReservation(uint16 _reservationID) public onlyServerOrOwner {
        // Verificando o Estado da Reserva:
        require(reservations[_reservationID].reservationID != 0, "ID da Reserva Invalido!");
        require(reservations[_reservationID].status != Status.CANCELLED, "Nao e Possivel Confirmar uma Reserva Cancelada!");
        require(reservations[_reservationID].status == Status.PENDING, "Nao e Possivel Confirmar uma Reserva Ja Confirmada ou Finalizada!");
        
        // Atualizando o Status da Reserva:
        reservations[_reservationID].status = Status.CONFIRMED;

        // Emitindo a Notificação:
        emit ReservationStatusUpdated(_reservationID, reservations[_reservationID].status);
    }

    // Marcando uma Reserva Como Paga:
    // A Função Será Usada Após a Gravação de Um Escrow de Pagamento.
    function markReservationAsPaid(uint16 _reservationID) public onlyServerOrOwner {
        // Verificando o Estado da Reserva:
        require(reservations[_reservationID].reservationID != 0, "ID da Reserva Invalido!");
        require(reservations[_reservationID].status != Status.CANCELLED, "Nao e Possivel Marcar uma Reserva Cancelada Como Paga!");
        require(reservations[_reservationID].status == Status.CONFIRMED, "Nao e Possivel Marcar uma Reserva Pendente de Confirmacao Como Paga");
        
        // Atualizando o Status da Reserva:
        reservations[_reservationID].status = Status.PAYED;
        
        // Emitindo a Notificação:
        emit ReservationStatusUpdated(_reservationID, reservations[_reservationID].status);
    }

    // Cancelando uma Reserva Existente:
    function cancelReservation(uint16 _reservationID) public onlyServerOrOwner {
        // Verificando o Estado da Reserva:
        require(reservations[_reservationID].reservationID != 0, "ID da Reserva Invalido!");
        require(reservations[_reservationID].status != Status.CANCELLED, "Nao e Possivel Cancelar uma Reserva Ja Cancelada!");
        require(reservations[_reservationID].status != Status.PAYED, "Nao e Possivel Cancelar uma Reserva Paga!");
        require(block.timestamp < reservations[_reservationID].startTimestamp, "Nao e Possivel Cancelar uma Reserva Ja Iniciada!");

        // Atualizando o Status da Reserva:
        reservations[_reservationID].status = Status.CANCELLED;

        // Emitindo a Notificação:
        emit ReservationStatusUpdated(_reservationID, reservations[_reservationID].status);
    }

    // Função para Auditar uma Reserva:
    function getReservation(uint16 _reservationID) public view returns (Reservation memory) {
        require(reservations[_reservationID].reservationID != 0, "ID da Reserva Invalido!");
        return reservations[_reservationID];
    }

    // Função para Retornar Auditar as Reservas de um Cliente:
    function getReservationsByCustomer(address _customerAddress) public view returns (Reservation[] memory){
        // Verificando o Endereço:
        require(_customerAddress != address(0), "Endereco do Usuario Invalido!");
        require(customerReservationIDs[_customerAddress].length > 0, "Usuario Sem Reservas Registradas!");
        
        // Obtendo Todas os IDs de Reserva Associadas a Este Cliente:
        uint16[] storage customerIDs = customerReservationIDs[_customerAddress];
        
        // Criando um Array em Memória para Armazenar as Structs de Reserva Completas:
        Reservation[] memory customerResList = new Reservation[](customerIDs.length);

        // Iterando Sobre as IDs e Preenchendo o Array de Structs:
        for (uint i = 0; i < customerIDs.length; i++) {
            customerResList[i] = reservations[customerIDs[i]];
        }

        return customerResList;
    }

    // Auditando Todas as Reservas do Contrato:
    function getAllReservations() public view returns (Reservation[] memory) {
        Reservation[] memory allResList = new Reservation[](nextReservationID - 1);
        for (uint16 i = 1; i < nextReservationID; i++) {
            allResList[i - 1] = reservations[i];
        }
        return allResList;
    }
}
