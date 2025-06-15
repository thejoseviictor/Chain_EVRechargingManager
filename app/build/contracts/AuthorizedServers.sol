// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract AuthorizedServers {
    // O Deployer do Contrato, Administrador:
    address public owner;

    // Mapeamento:
    mapping(address => bool) public authorizedRechargingServers;

    // Evento para Notificação:
    event AuthorizedRechargingServersUpdate(address indexed server, bool status);

    // Modificadores:
    modifier onlyOwner() {
        require(msg.sender == owner, "Apenas o Administrador Pode Executar Esta Acao!");
        _;
    }

    // Construtor:
    constructor() {
        owner = msg.sender;
    }

    // Função para Autorizar um Servidor de Posto de Carregamento:
    function authorizeRechargingServer(address _server) public onlyOwner {
        authorizedRechargingServers[_server] = true;
        emit AuthorizedRechargingServersUpdate(_server, true);
    }

    // Verificando Se Um Servidor de Posto de Carregamento Está Autorizado:
    function isAuthorizedRechargingServer(address _serverAddress) public view returns (bool) {
        return authorizedRechargingServers[_serverAddress];
    }
}
