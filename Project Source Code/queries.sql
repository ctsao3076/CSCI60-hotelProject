--Q1: Currently occupied rooms  with guest info
SELECT r.roomNumber, c.firstName ||''|| c.lastName AS guest, 
ra.actualCheckIn, w.wingDesignation
FROM room_assignment ra 
JOIN room r ON ra.roomId = r.roomId
JOIN wing w ON r.wingId = w.wingId 
WHERE ra.isActive = 1; 

--Q2: Rooms available righ now 
SELECT w.wingDesignation, r.roomType, r.roomNumber, r.baseRentalRate
FROM room r 
JOIN wing w ON r.wingId = w.wingId
WHERE r.status = 'AVAILABLE'
AND r.roomId NOT IN (
    SELECT roomId FROM room_assignment WHERE isActive = 1
)
ORDER BY w.wingSequenceNumber, r.roomNumber

--Q3: Total Changes per customer, sorted by highest spend 
SELECT c.customerId, c.firstName ||''|| c.lastName AS name, 
COUNT(ch.chargeId) AS numCharges, 
SUM(ch.amount) AS totalSpend
FROM costumer c 
JOIN charge ch ON c.costumerId = ch.billedPartyId
GROUP BY c.costumerId
ORDER BY totalSpend DESC; 

--Q4: Unpaid / pending charges for a costumer 
SELECT c.firstName ||''|| c.lastName AS name, 
ch.chargeType, ch.chargeDescription, 
ch.amount, ch.chargeStatus 
FROM charge ch 
JOIN customer c ON ch.billedPartyId = c.customerId
WHERE ch.chargeStatus IN ('ACTUAL', 'ORDERED', 'AUTHORIZED')
ORDER BY c.lastName, ch.chargeDatetime; 

--Q5: Upcoming events with host name and attendance 
SELECT e.eventName, c.firstName ||''|| c.lastName AS host, 
e.startDatetime, e.estimatedAttendance, 
e.estimatedHotelGuests, e.eventStatus
FROM event e 
JOIN customer c ON e.hostCustomerId = c.customerId
WHERE e.startDatetime > datetime('now')
ORDER BY e.startDatetime; 

--Q6: Rooms booked per Event 
SELECT e.eventName, COUNT(DISTINCT er.roomId) AS roomsUsed, 
COUNT(er.eventRoomId) AS totalSlotBookings, 
SUM(er.chargeRate) AS totalCharges 
FROM event e 
JOIN event_room er ON e.evntId = er.eventRoomId
GROUP BY e.eventId, e.eventName; 

--Q7: Reservations Missing Required Deposits 
SELECT r.reservationId, c.firstName ||''|| c.lastName AS name, 
r.checkInDate, r.advanceDepositAmount, 
r.reservationStatus
FROM reservation r 
JOIN costumer c ON r.coustumerId = c.customerId

--Q8: Smoking rooms near pool, sorted by rate
SELECT r.roomNumber, r.roomType, r.baseRentalRate,
  w.wingDesignation,
  w.hasPool
FROM room r
JOIN wing w ON r.wingId = w.wingId
WHERE r.isSmoking = 1
  AND w.hasPool = 1
ORDER BY r.baseRentalRate;

--Q9: Available rooms with amenities for a given date range
-- Replace '2026-04-15' and '2026-04-20' with target dates
SELECT r.roomNumber, r.roomType, r.baseRentalRate,
  r.hasTV, r.hasPhone, r.hasKitchenette,
  r.isSmoking, r.isHandicapped,
  w.wingDesignation
FROM room r
JOIN wing w ON r.wingId = w.wingId
WHERE r.status = 'AVAILABLE'
  AND r.roomType = 'SLEEPING'
  AND r.roomId NOT IN (
    SELECT ra.roomId FROM room_assignment ra
    JOIN reservation res ON ra.reservationId = res.reservationId
    WHERE res.checkInDate  < '2026-04-20'
      AND res.checkOutDate > '2026-04-15'
  )
ORDER BY r.baseRentalRate;

--Q10: Rooms that can sleep a specific number of guests
-- Replace 2 with desired guest count
SELECT r.roomNumber, r.roomType,
  r.maxOccupancy, r.baseRentalRate,
  w.wingDesignation
FROM room r
JOIN wing w ON r.wingId = w.wingId
WHERE r.maxOccupancy >= 2
  AND r.roomType IN ('SLEEPING', 'SUITE')
ORDER BY r.maxOccupancy, r.baseRentalRate;

--Q11: Bed types available per room
SELECT r.roomNumber, r.roomType,
  rb.bedSize, rb.bedQuality,
  r.baseRentalRate
FROM room r
JOIN room_bed rb ON r.roomId = rb.roomId
ORDER BY r.roomNumber, rb.bedSize;

--Q12: Guest full stay history
SELECT c.firstName ||' '|| c.lastName AS guest,
  r.roomNumber, r.roomType,
  ra.actualCheckIn, ra.actualCheckOut,
  res.reservationStatus,
  SUM(ch.amount) AS totalCharged
FROM customer c
JOIN room_assignment ra ON c.customerId = ra.guestId
JOIN room r ON ra.roomId = r.roomId
JOIN reservation res ON ra.reservationId = res.reservationId
LEFT JOIN charge ch ON ch.billedPartyId = c.customerId
GROUP BY c.customerId, ra.assignmentId
ORDER BY c.lastName, ra.actualCheckIn;

--Q13: All facilities at the complex
SELECT f.facilityName, f.facilityType,
  f.locationDescription,
  hc.complexName
FROM facility f
JOIN hotel_complex hc ON f.complexId = hc.complexId
ORDER BY f.facilityType, f.facilityName;


-- Application Queries

--A1: Home page Summary
SELECT (SELECT COUNT(*) FROM room) AS totalRooms,
(SELECT COUNT(*) FROM room_assignment WHERE isActive = 1) AS occupiedRooms,
(SELECT COUNT(*) FROM reservation WHERE reservationStatus IN ('CONFIRMED', 'PENDING')) AS openReservations,
(SELECT COUNT(*) FROM event WHERE startDatetime > datetime('now')) AS upcomingEvents,
(SELECT COUNT(*) FROM customer) AS totalCustomers;

SELECT * FROM hotel_complex LIMIT 1;

--A2: Search Bar
SELECT customerId, firstName ||' '|| lastName AS name, email, phone
FROM customer
WHERE lower(firstName ||' '|| lastName) LIKE lower('%:term%')
OR lower(email) LIKE lower('%:term%')
ORDER BY lastName, firstName;

SELECT r.roomNumber, r.roomType, r.status, r.baseRentalRate, w.wingDesignation
FROM room r
JOIN wing w ON r.wingId = w.wingId
WHERE CAST(r.roomNumber AS TEXT) LIKE '%:term%'
OR lower(r.roomType) LIKE lower('%:term%')
ORDER BY w.wingSequenceNumber, r.roomNumber;


--A3: Rooms Showcase
SELECT r.roomId, r.roomNumber, r.roomType, r.baseRentalRate,
r.maxSleepingGuests, r.status,
w.wingDesignation, b.buildingName
FROM room r
JOIN wing w ON r.wingId = w.wingId
JOIN building b ON w.buildingId = b.buildingId
ORDER BY r.roomType, w.wingSequenceNumber, r.roomNumber;

SELECT roomType, COUNT(*) AS n, MIN(baseRentalRate) AS minRate
FROM room
GROUP BY roomType;

--A4: Amenities Showcase 
SELECT f.facilityId, f.facilityName, f.facilityType,
f.locationDescription, hc.complexName
FROM facility f
JOIN hotel_complex hc ON f.complexId = hc.complexId
ORDER BY f.facilityType, f.facilityName;

--A5a: Operations Dashboard 
SELECT COALESCE(SUM(amount), 0) AS lifetimeRevenue FROM charge;

SELECT COUNT(*) AS totalRooms FROM room;
SELECT COUNT(*) AS occupiedRooms FROM room_assignment WHERE isActive = 1;

SELECT COUNT(*) AS totalGuests FROM customer;

SELECT COUNT(*) AS repeatGuests
FROM (
    SELECT guestId FROM room_assignment
    WHERE guestId IS NOT NULL
    GROUP BY guestId
    HAVING COUNT(*) > 1
);

--A5b: Dashboard — Revenue Growth Per Month
SELECT strftime('%Y-%m', chargeDatetime) AS ym,
SUM(amount) AS monthlyRevenue
FROM charge
WHERE chargeDatetime IS NOT NULL
GROUP BY ym
ORDER BY ym;

--A5c: Dashboard — Occupancy Rate
SELECT COUNT(*) AS available FROM room WHERE status = 'AVAILABLE';

SELECT COUNT(*) AS underMaintenance FROM room
WHERE status IN ('RENOVATION', 'MAINTENANCE', 'OUT_OF_SERVICE', 'NEEDS_CLEANING');

--A5d: Dashboard Revenue by Charge Type
SELECT chargeType, COALESCE(SUM(amount), 0) AS revenue
FROM charge
GROUP BY chargeType
ORDER BY revenue DESC;

--A5e: Dashboard — Loyalty Distribution
SELECT guestId, COUNT(*) AS stays
FROM room_assignment
WHERE guestId IS NOT NULL
GROUP BY guestId;

--A5f: Dashboard — Top Loyal Guests
SELECT c.firstName ||' '|| c.lastName AS name,
COUNT(ra.assignmentId) AS stays,
COALESCE(SUM(ch.amount), 0) AS spend
FROM customer c
LEFT JOIN room_assignment ra ON ra.guestId = c.customerId
LEFT JOIN charge ch ON ch.billedPartyId = c.customerId
GROUP BY c.customerId
HAVING stays > 0
ORDER BY stays DESC, spend DESC
LIMIT 6;

--A6a: Manage Guests 
SELECT c.customerId,
c.firstName ||' '|| c.lastName AS name,
c.email, c.phone,
COALESCE(s.stays, 0) AS stays,
CASE WHEN a.activeId IS NOT NULL THEN 1 ELSE 0 END AS activeStay
FROM customer c
LEFT JOIN (
    SELECT guestId, COUNT(*) AS stays
    FROM room_assignment
    GROUP BY guestId
) s ON s.guestId = c.customerId
LEFT JOIN (
    SELECT guestId, MAX(assignmentId) AS activeId
    FROM room_assignment
    WHERE isActive = 1
    GROUP BY guestId
) a ON a.guestId = c.customerId
ORDER BY c.lastName, c.firstName;

--A6b: Manage Guests - delete 
DELETE FROM billing_split WHERE customerId = :customerId;

DELETE FROM billing_split
WHERE roomAssignmentId IN (
    SELECT assignmentId FROM room_assignment WHERE guestId = :customerId
);

DELETE FROM charge WHERE billedPartyId = :customerId;

DELETE FROM charge
WHERE roomAssignmentId IN (
    SELECT assignmentId FROM room_assignment WHERE guestId = :customerId
);

DELETE FROM reservation_preference
WHERE reservationId IN (
    SELECT reservationId FROM reservation WHERE customerId = :customerId
);

DELETE FROM room_assignment WHERE guestId = :customerId;
DELETE FROM reservation WHERE customerId = :customerId;
DELETE FROM event_guest WHERE customerId = :customerId;

DELETE FROM card_scan_log
WHERE cardId IN (
    SELECT cardId FROM guest_card WHERE customerId = :customerId
);

DELETE FROM guest_card WHERE customerId = :customerId;
DELETE FROM guest_message WHERE customerId = :customerId;
DELETE FROM customer WHERE customerId = :customerId;

--A7a: Room Change 
UPDATE room_assignment
SET isActive = 0,
    actualCheckOut = :now
WHERE assignmentId = :assignmentId;

UPDATE room
SET status = 'NEEDS_CLEANING',
    statusUpdatedAt = :now
WHERE roomId = (
    SELECT roomId FROM room_assignment WHERE assignmentId = :assignmentId
);

INSERT INTO room_assignment
(reservationId, roomId, guestId, assignedDate, actualCheckIn, isActive)
SELECT reservationId, :newRoomId, guestId, :now,
COALESCE(actualCheckIn, :now), 1
FROM room_assignment
WHERE assignmentId = :assignmentId;

UPDATE room
SET status = 'OCCUPIED',
    statusUpdatedAt = :now
WHERE roomId = :newRoomId;


--A8: Add Reservation 
INSERT INTO reservation
(customerId, eventId, reservationDate, checkInDate, checkOutDate,
numGuests, reservationStatus,
advanceDepositRequired, advanceDepositAmount, depositPaid)
VALUES
(:customerId, :eventId, :reservationDate, :checkInDate, :checkOutDate,
:numGuests, :reservationStatus,
:advanceDepositRequired, :advanceDepositAmount, :depositPaid);


--A9: Add Customer 
SELECT organizationId, orgName FROM organization ORDER BY orgName;

INSERT INTO customer
(firstName, lastName, email, phone, address,
organizationId, qualificationRating, paymentPromptness,
confidentialLocation)
VALUES
(:firstName, :lastName, :email, :phone, :address,
:organizationId, :qualificationRating, :paymentPromptness,
:confidentialLocation);









