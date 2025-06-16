// SPDX-License-Identifier: MIT
pragma solidity >=0.8.2 <0.9.0;

// Importando as Dependências dos Outros Contratos:
import "./AuthorizedServers.sol";
import "./ReservationLedger.sol";

contract TransactionLedger {
    // O Deployer do Contrato, Administrador:
    address public owner;

    // Referência aos Contratos "AuthorizedServers" e "ReservationLedger":
    AuthorizedServers public authorizedServers;
    ReservationLedger public reservationLedger;

    // Dados da Transação:
    struct TransactionRecord {
        uint256 transactionID;
        uint256 reservationID;
        uint256 price; // Preço da Transação em "wei".
        address payer; // Endereço da Carteira que Efetuou o Pagamento.
        bool paid; // Indica Se o Pagamento foi Confirmado.
        uint256 transactionTimestamp;
    }

    // Mapeamento:
    mapping(uint256 => TransactionRecord) public transactionRecords;

    // Contador de IDs:
    uint256 public nextTransactionID;

    // Evento para Notificação:
    event TransactionRecorded(
        uint256 indexed transactionID,
        uint256 reservationID,
        address payer,
        uint256 price
    );

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
        nextTransactionID = 1;
    }

    /**
     * Registrando, Imutavelmente, uma Transação de Pagamento Auditável de Reserva no Ledger.
     * Supõe-se que o Pagamento Real (Transferência de ETH/Tokens) Ocorreu.
     * Estamos Apenas Registrando a Operação.
     */
    function recordTransaction(
        uint256 _reservationID,
        address _payer, // Endereço da Carteira Pagante.
        bool _paid // Status de Pagamento: "true" ou "false".
    ) public onlyServerOrOwner returns (uint256) {
        // Verificando o Estado da Reserva:
        ReservationLedger.Reservation memory reservation = reservationLedger.getReservation(_reservationID);
        require(reservation.reservationID != 0, "ID da Reserva Invalido!");
        require(reservation.status != ReservationLedger.Status.CANCELLED, "Nao e Possivel Registrar o Pagamento de uma Reserva Cancelada!");
        require(reservation.status != ReservationLedger.Status.PENDING, "Nao e Possivel Registrar o Pagamento de uma Reserva Pendente!");
        require(reservation.status != ReservationLedger.Status.PAYED, "Nao e Possivel Registrar o Pagamento de uma Reserva Paga!");

        // Criando a Transação:
        uint256 newTransactionID = nextTransactionID;
        transactionRecords[newTransactionID] = TransactionRecord({
            transactionID: newTransactionID,
            reservationID: _reservationID,
            price: reservation.price,
            payer: _payer,
            paid: _paid,
            transactionTimestamp: block.timestamp
        });

        // Incrementando o ID Para a Próxima Transação:
        nextTransactionID++;

        // Emitindo a Notificação da Transação:
        emit TransactionRecorded(
            newTransactionID,
            _reservationID,
            _payer,
            reservation.price
        );

        // Retornando o ID da Transação:
        return newTransactionID;
    }

    // Função para Auditar uma Transação:
    function getTransactionRecord(uint256 _transactionID) public view returns (TransactionRecord memory) {
        require(transactionRecords[_transactionID].transactionID != 0, "ID de Transacao Nao Encontrado!");
        return transactionRecords[_transactionID];
    }
}
