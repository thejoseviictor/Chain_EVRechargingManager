// SPDX-License-Identifier: MIT
pragma solidity 0.8.0;

// Importando as Dependências dos Outros Contratos:
import "./AuthorizedServers.sol";
import "./ReservationLedger.sol";

contract ChargingSessionManager {
    // O Deployer do Contrato, Administrador:
    address public owner;

    // Referência aos Contratos "AuthorizedServers" e "ReservationLedger":
    AuthorizedServers public authorizedServers;
    ReservationLedger public reservationLedger;

    // Status da Sessão de Recarga:
    enum SessionStatus {IDLE, IN_PROGRESS, FINISHED}

    // Dados da Sessão de Recarga:
    struct ChargingSession {
        uint16 reservationID;
        address customer;
        SessionStatus status;
    }

    // Mapeamento:
    mapping(uint16 => ChargingSession) public chargingSessions; // Até 65536 Sessões de Carregamento Possíveis.

    // Evento para Notificação:
    event SessionStatusUpdated(uint16 indexed reservationID, SessionStatus status);

    // Modificador:
    modifier onlyServerOrOwner() {
        require(authorizedServers.isAuthorizedRechargingServer(msg.sender) || msg.sender == owner, "Apenas um Dos Servidores de Carregamento ou Administrador Pode Executar Esta Acao!");
        _;
    }

    // Construtor:
    constructor(address _authorizedServersAddress, address _reservationLedgerAddress) {
        owner = msg.sender;
        authorizedServers = AuthorizedServers(_authorizedServersAddress);
        reservationLedger = ReservationLedger(_reservationLedgerAddress);
    }

    // Iniciando uma Sessão de Recarga Para Uma Reserva Paga:
    function startChargingSession(
        uint16 _reservationID
    ) public onlyServerOrOwner {
        // Recuperando os Dados da Reserva:
        ReservationLedger.Reservation memory rs = reservationLedger.getReservation(_reservationID);

        // Verificando as Informações da Reserva e Pagamento:
        require(rs.reservationID != 0, "ID da Reserva Invalido!");
        require(rs.status == ReservationLedger.Status.PAYED, "Os Fundos Nao Foram Depositados Para Esta Reserva!");
        
        // Verificando as Informações da Sessão de Recarga da Reserva:
        require(chargingSessions[_reservationID].reservationID == 0, "Sessao de Recarga Ja Iniciada Para Esta Reserva!");

        // Criando a Nova Sessão de Recarga:
        chargingSessions[_reservationID] = ChargingSession({
            reservationID: _reservationID,
            customer: rs.customer,
            status: SessionStatus.IN_PROGRESS
        });

        // Emitindo uma Notificação:
        emit SessionStatusUpdated(_reservationID, SessionStatus.IN_PROGRESS);
    }

    // Finalizando uma Sessão de Recarga:
    function finishChargingSession(
        uint16 _reservationID
    ) public onlyServerOrOwner {
        // Verificando as Informações da Recarga:
        ChargingSession storage session = chargingSessions[_reservationID];
        require(session.reservationID != 0, "Sessao de Recarga Nao Encontrada Para Esta Reserva!");
        require(session.status == SessionStatus.IN_PROGRESS, "A Sessao Nao Esta Em Andamento!");

        // Atualizando o Status da Sessão de Recarga:
        session.status = SessionStatus.FINISHED;

        // Emitindo uma Notificação:
        emit SessionStatusUpdated(_reservationID, SessionStatus.FINISHED);
    }

    // Auditando os Detalhes de Uma Sessão de Recarga:
    function getChargingSession(uint16 _reservationID) public view returns (ChargingSession memory) {
        require(chargingSessions[_reservationID].reservationID != 0, "Sessao de Recarga Nao Encontrada!");
        return chargingSessions[_reservationID];
    }
}
