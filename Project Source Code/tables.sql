PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS guest_message;
DROP TABLE IF EXISTS card_scan_log;
DROP TABLE IF EXISTS card_reader;
DROP TABLE IF EXISTS guest_card;
DROP TABLE IF EXISTS facility;
DROP TABLE IF EXISTS billing_split;
DROP TABLE IF EXISTS charge;
DROP TABLE IF EXISTS time_slot;
DROP TABLE IF EXISTS event_guest;
DROP TABLE IF EXISTS event_room;
DROP TABLE IF EXISTS room_assignment;
DROP TABLE IF EXISTS reservation_preference;
DROP TABLE IF EXISTS reservation;
DROP TABLE IF EXISTS event;
DROP TABLE IF EXISTS customer;
DROP TABLE IF EXISTS organization;
DROP TABLE IF EXISTS room_adjacency;
DROP TABLE IF EXISTS room_bed;
DROP TABLE IF EXISTS room;
DROP TABLE IF EXISTS floor;
DROP TABLE IF EXISTS wing;
DROP TABLE IF EXISTS building;
DROP TABLE IF EXISTS hotel_complex;

-- Hotel Complex
CREATE TABLE hotel_complex (
    complexId INTEGER PRIMARY KEY,
    complexName TEXT NOT NULL,
    address TEXT NOT NULL,
    city TEXT NOT NULL,
    state TEXT NOT NULL,
    country TEXT NOT NULL,
    phone TEXT
);

-- Building
CREATE TABLE building (
    buildingId INTEGER PRIMARY KEY,
    complexId INTEGER NOT NULL,
    buildingName TEXT NOT NULL,
    FOREIGN KEY (complexId) REFERENCES hotel_complex(complexId)
);

-- Wing
CREATE TABLE wing (
    wingId INTEGER PRIMARY KEY,
    buildingId INTEGER NOT NULL,
    wingDesignation TEXT NOT NULL,
    wingSequenceNumber INTEGER NOT NULL,
    poolProximity INTEGER CHECK (poolProximity IN (0, 1)),
    parkingProximity INTEGER CHECK (parkingProximity IN (0, 1)),
    handicappedAccess INTEGER CHECK (handicappedAccess IN (0, 1)),
    FOREIGN KEY (buildingId) REFERENCES building(buildingId)
);

-- Floor
CREATE TABLE floor (
    floorId INTEGER PRIMARY KEY,
    wingId INTEGER NOT NULL,
    floorNumber INTEGER NOT NULL,
    isNonsmokingFloor INTEGER CHECK (isNonsmokingFloor IN (0, 1)),
    FOREIGN KEY (wingId) REFERENCES wing(wingId)
);

-- Room
CREATE TABLE room (
    roomId INTEGER PRIMARY KEY,
    wingId INTEGER NOT NULL,
    floorId INTEGER NOT NULL,
    roomNumber INTEGER NOT NULL,
    roomType TEXT NOT NULL,
    baseRentalRate INTEGER NOT NULL,
    hasToilet INTEGER CHECK (hasToilet IN (0, 1)),
    hasBath INTEGER CHECK (hasBath IN (0, 1)),
    hasTelephone INTEGER CHECK (hasTelephone IN (0, 1)),
    hasTelevision INTEGER CHECK (hasTelevision IN (0, 1)),
    hasCloset INTEGER CHECK (hasCloset IN (0, 1)),
    hasFoldawayBed INTEGER CHECK (hasFoldawayBed IN (0, 1)),
    hasPermanentBeds INTEGER CHECK (hasPermanentBeds IN (0, 1)),
    isSmoking INTEGER CHECK (isSmoking IN (0, 1)),
    status TEXT NOT NULL,
    statusUpdatedAt TEXT NOT NULL,
    maxSleepingGuests INTEGER,
    allowsRollaway INTEGER CHECK (allowsRollaway IN (0, 1)),
    seatingCapacity INTEGER,
    isOutdoor INTEGER CHECK (isOutdoor IN (0, 1)),
    hasMoveableWalls INTEGER CHECK (hasMoveableWalls IN (0, 1)),
    numSubdivisions INTEGER,
    FOREIGN KEY (wingId) REFERENCES wing(wingId),
    FOREIGN KEY (floorId) REFERENCES floor(floorId),
    UNIQUE (wingId, roomNumber)
);

-- Room Bed
CREATE TABLE room_bed (
    roomBedId INTEGER PRIMARY KEY,
    roomId INTEGER NOT NULL,
    bedType TEXT NOT NULL,
    bedSize TEXT NOT NULL,
    FOREIGN KEY (roomId) REFERENCES room(roomId)
);

-- Room Adjacency
CREATE TABLE room_adjacency (
    roomId1 INTEGER NOT NULL,
    roomId2 INTEGER NOT NULL,
    hasPrivateDoor INTEGER NOT NULL CHECK (hasPrivateDoor IN (0, 1)),
    doorType TEXT,
    PRIMARY KEY (roomId1, roomId2),
    FOREIGN KEY (roomId1) REFERENCES room(roomId),
    FOREIGN KEY (roomId2) REFERENCES room(roomId),
    CHECK (roomId1 < roomId2)
);

-- Organization (created before customer to avoid circular FK issue)
CREATE TABLE organization (
    organizationId INTEGER PRIMARY KEY,
    orgName TEXT NOT NULL,
    orgAddress TEXT,
    orgPhone TEXT,
    contactPersonId INTEGER
);

-- Customer
CREATE TABLE customer (
    customerId INTEGER PRIMARY KEY,
    firstName TEXT NOT NULL,
    lastName TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT NOT NULL,
    address TEXT,
    organizationId INTEGER,
    qualificationRating TEXT,
    cooperativenessNotes TEXT,
    paymentPromptness TEXT,
    confidentialLocation INTEGER CHECK (confidentialLocation IN (0, 1)),
    FOREIGN KEY (organizationId) REFERENCES organization(organizationId)
);

-- Event
CREATE TABLE event (
    eventId INTEGER PRIMARY KEY,
    eventName TEXT NOT NULL,
    hostCustomerId INTEGER,
    billedPartyId INTEGER,
    startDatetime TEXT NOT NULL,
    endDatetime TEXT NOT NULL,
    estimatedAttendance INTEGER,
    estimatedHotelGuests INTEGER,
    eventStatus TEXT NOT NULL,
    FOREIGN KEY (hostCustomerId) REFERENCES customer(customerId),
    FOREIGN KEY (billedPartyId) REFERENCES customer(customerId)
);

-- Reservation
CREATE TABLE reservation (
    reservationId INTEGER PRIMARY KEY,
    customerId INTEGER NOT NULL,
    eventId INTEGER,
    reservationDate TEXT NOT NULL,
    checkInDate TEXT NOT NULL,
    checkOutDate TEXT NOT NULL,
    numGuests INTEGER NOT NULL,
    reservationStatus TEXT,
    advanceDepositRequired INTEGER CHECK (advanceDepositRequired IN (0, 1)),
    advanceDepositAmount INTEGER,
    depositPaid INTEGER CHECK (depositPaid IN (0, 1)),
    FOREIGN KEY (customerId) REFERENCES customer(customerId),
    FOREIGN KEY (eventId) REFERENCES event(eventId)
);

-- Reservation Preference
CREATE TABLE reservation_preference (
    preferenceId INTEGER PRIMARY KEY,
    reservationId INTEGER NOT NULL,
    preferenceType TEXT NOT NULL,
    preferenceValue TEXT NOT NULL,
    FOREIGN KEY (reservationId) REFERENCES reservation(reservationId)
);

-- Room Assignment
CREATE TABLE room_assignment (
    assignmentId INTEGER PRIMARY KEY,
    reservationId INTEGER,
    roomId INTEGER,
    guestId INTEGER,
    assignedDate TEXT NOT NULL,
    actualCheckIn TEXT,
    actualCheckOut TEXT,
    earlyLateExtension INTEGER CHECK (earlyLateExtension IN (0, 1)),
    extensionHours INTEGER,
    extensionSurcharge INTEGER,
    isActive INTEGER CHECK (isActive IN (0, 1)),
    FOREIGN KEY (reservationId) REFERENCES reservation(reservationId),
    FOREIGN KEY (roomId) REFERENCES room(roomId),
    FOREIGN KEY (guestId) REFERENCES customer(customerId)
);

-- Event Room
CREATE TABLE event_room (
    eventRoomId INTEGER PRIMARY KEY,
    eventId INTEGER,
    roomId INTEGER,
    timeSlotId INTEGER,
    usageDate TEXT NOT NULL,
    isComplimentary INTEGER CHECK (isComplimentary IN (0, 1)),
    chargeRate INTEGER,
    rateWaived INTEGER CHECK (rateWaived IN (0, 1)),
    FOREIGN KEY (eventId) REFERENCES event(eventId),
    FOREIGN KEY (roomId) REFERENCES room(roomId),
    FOREIGN KEY (timeSlotId) REFERENCES time_slot(timeSlotId)
);

-- Event Guest
CREATE TABLE event_guest (
    eventId INTEGER NOT NULL,
    customerId INTEGER NOT NULL,
    role TEXT NOT NULL,
    PRIMARY KEY (eventId, customerId),
    FOREIGN KEY (eventId) REFERENCES event(eventId),
    FOREIGN KEY (customerId) REFERENCES customer(customerId)
);

-- Time Slot
CREATE TABLE time_slot (
    timeSlotId INTEGER PRIMARY KEY,
    slotName TEXT NOT NULL,
    startTime TEXT,
    endTime TEXT,
    isEatingSlot INTEGER CHECK (isEatingSlot IN (0, 1))
);

-- Charge
CREATE TABLE charge (
    chargeId INTEGER PRIMARY KEY,
    billedPartyId INTEGER,
    roomAssignmentId INTEGER,
    chargeType TEXT NOT NULL,
    chargeDescription TEXT NOT NULL,
    amount INTEGER,
    chargeDatetime TEXT NOT NULL,
    recordedDatetime TEXT NOT NULL,
    chargeStatus TEXT NOT NULL,
    FOREIGN KEY (billedPartyId) REFERENCES customer(customerId),
    FOREIGN KEY (roomAssignmentId) REFERENCES room_assignment(assignmentId)
);

-- Billing Split
CREATE TABLE billing_split (
    splitId INTEGER PRIMARY KEY,
    roomAssignmentId INTEGER,
    customerId INTEGER,
    splitType TEXT NOT NULL,
    splitPercentage INTEGER,
    splitAmount INTEGER,
    FOREIGN KEY (roomAssignmentId) REFERENCES room_assignment(assignmentId),
    FOREIGN KEY (customerId) REFERENCES customer(customerId)
);

-- Facility
CREATE TABLE facility (
    facilityId INTEGER PRIMARY KEY,
    complexId INTEGER,
    facilityName TEXT NOT NULL,
    facilityType TEXT NOT NULL,
    locationDescription TEXT NOT NULL,
    FOREIGN KEY (complexId) REFERENCES hotel_complex(complexId)
);

-- Guest Card
CREATE TABLE guest_card (
    cardId INTEGER PRIMARY KEY,
    customerId INTEGER,
    pin INTEGER,
    cardType TEXT NOT NULL,
    issuedDate TEXT NOT NULL,
    isActive INTEGER CHECK (isActive IN (0, 1)),
    FOREIGN KEY (customerId) REFERENCES customer(customerId)
);

-- Card Reader
CREATE TABLE card_reader (
    readerId INTEGER PRIMARY KEY,
    roomId INTEGER,
    facilityId INTEGER,
    readerLocation TEXT NOT NULL,
    FOREIGN KEY (roomId) REFERENCES room(roomId),
    FOREIGN KEY (facilityId) REFERENCES facility(facilityId)
);

-- Card Scan Log
CREATE TABLE card_scan_log (
    scanId INTEGER PRIMARY KEY,
    cardId INTEGER,
    readerId INTEGER,
    scanDatetime TEXT NOT NULL,
    direction TEXT NOT NULL,
    FOREIGN KEY (cardId) REFERENCES guest_card(cardId),
    FOREIGN KEY (readerId) REFERENCES card_reader(readerId)
);

-- Guest Message
CREATE TABLE guest_message (
    messageId INTEGER PRIMARY KEY,
    customerId INTEGER,
    messageType TEXT NOT NULL,
    messageContent TEXT NOT NULL,
    senderName TEXT,
    senderPhone TEXT,
    createdDatetime TEXT NOT NULL,
    isRead INTEGER CHECK (isRead IN (0, 1)),
    FOREIGN KEY (customerId) REFERENCES customer(customerId)
);
