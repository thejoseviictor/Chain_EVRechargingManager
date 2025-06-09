// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract ReservationLedger {
    // Status da Reserva:
    enum Status { Pending, Confirmed, Completed, Cancelled }

    // Estrutura de uma Reserva:
    struct Reservation {
        uint256 reservationID;
        uint256 chargingStationID;
        uint256 chargingPointID;
        string cityName;
        string cityCodename;
        string companyName;
        uint256 chargingPointPower;
        uint256 kWhPrice; // Em "wei", menor unidade de valor do Ethereum.
        uint256 vehicleID;
        uint256 startDateTime; // Converter ISO para "timestamp".
        uint256 finishDateTime;
        uint256 duration;
        uint256 price; // Em "wei".
        Status status;
        address customer;
    }

    uint256 public nextReservationID = 1;

    mapping(uint256 => Reservation) public reservations;
    mapping(address => uint256[]) public reservationsByCustomer;

    event ReservationCreated(uint256 reservationID, address customer);
    event ReservationStatusUpdated(uint256 reservationID, Status status)
    event PaymentReleased(uint256 reservationID, uint256 amount, address to)
}
