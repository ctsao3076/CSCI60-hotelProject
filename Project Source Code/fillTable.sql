-- hotel_complex
INSERT INTO hotel_complex VALUES (1, 'Last Resort Miami', '100 Ocean Dr', 'Miami', 'FL', 'USA', '305-555-0001');

-- building
INSERT INTO building VALUES (1, 1, 'Ocean Tower');
INSERT INTO building VALUES (2, 1, 'Palm Wing');
INSERT INTO building VALUES (3, 1, 'Coral Building');

-- wing
INSERT INTO wing VALUES (1, 1, 'A', 1, 1, 0, 1);
INSERT INTO wing VALUES (2, 1, 'B', 2, 0, 1, 0);
INSERT INTO wing VALUES (3, 2, 'A', 1, 1, 1, 1);

-- floor
INSERT INTO floor VALUES (1, 1, 1, 0);
INSERT INTO floor VALUES (2, 1, 2, 1);
INSERT INTO floor VALUES (3, 2, 1, 0);

-- room
INSERT INTO room VALUES (1, 1, 1, 101, 'SLEEPING', 250, 1, 1, 1, 1, 1, 0, 1, 0, 'AVAILABLE', '2026-03-30 08:00:00', 2, 1, NULL, NULL, NULL, NULL);
INSERT INTO room VALUES (2, 1, 2, 201, 'MEETING', 500, 1, 0, 1, 0, 0, 0, 0, 0, 'AVAILABLE', '2026-03-30 08:00:00', NULL, NULL, 100, 0, 1, 3);
INSERT INTO room VALUES (3, 2, 3, 102, 'SUITE', 400, 1, 1, 1, 1, 1, 1, 0, 0, 'OCCUPIED', '2026-03-31 14:00:00', 2, 1, 20, 0, 0, NULL);

-- room_bed
INSERT INTO room_bed VALUES (1, 1, 'KING', 'DOUBLE');
INSERT INTO room_bed VALUES (2, 1, 'QUEEN', 'DOUBLE');
INSERT INTO room_bed VALUES (3, 3, 'KING', 'DOUBLE');

-- room_adjacency
INSERT INTO room_adjacency VALUES (1, 2, 1, 'PRIVATE');
INSERT INTO room_adjacency VALUES (1, 3, 0, 'MOVABLE_WALL');
INSERT INTO room_adjacency VALUES (2, 3, 1, 'PRIVATE');

-- customer (before organization so contactPersonId refs work)
INSERT INTO customer VALUES (1, 'Maria', 'Santos', 'maria@acme.com', '305-555-1001', '10 Palm St, Miami FL', NULL, 'EXCELLENT', NULL, 'EXCELLENT', 0);
INSERT INTO customer VALUES (2, 'James', 'Chen', 'james.chen@gmail.com', '305-555-2001', '45 Collins Ave, Miami FL', NULL, 'GOOD', NULL, 'GOOD', 0);
INSERT INTO customer VALUES (3, 'Priya', 'Patel', 'priya@gmail.com', '305-555-3001', '800 Biscayne Blvd, Miami FL', NULL, 'NEW', NULL, 'FAIR', 1);
INSERT INTO customer VALUES (4, 'David', 'Kim', 'david@globalevents.com', '305-555-2002', '90 Brickell Ave, Miami FL', NULL, 'EXCELLENT', 'Very cooperative, flexible with scheduling', 'EXCELLENT', 0);
INSERT INTO customer VALUES (5, 'Sarah', 'Johnson', 'sarah.j@email.com', '305-555-1005', '220 Brickell Ave, Miami FL', NULL, 'GOOD', NULL, 'GOOD', 0);
INSERT INTO customer VALUES (6, 'Mike', 'Brown', 'mike.b@email.com', '305-555-1006', '15 Collins Ave, Miami FL', NULL, 'FAIR', 'Late payments twice', 'POOR', 0);
INSERT INTO customer VALUES (7, 'Lisa', 'Wang', 'lisa@techstart.com', '305-555-3002', '900 Coral Way, Miami FL', NULL, 'GOOD', NULL, 'EXCELLENT', 0);

-- organization (after customer)
INSERT INTO organization VALUES (1, 'Acme Corp', '500 Business Pkwy, Miami FL', '305-555-1000', 1);
INSERT INTO organization VALUES (2, 'Global Events LLC', '88 Brickell Ave, Miami FL', '305-555-2000', 4);
INSERT INTO organization VALUES (3, 'TechStart Inc', '1200 Coral Way, Miami FL', '305-555-3000', 7);

-- update customers with their organizationId now that orgs exist
UPDATE customer SET organizationId = 1 WHERE customerId = 1;
UPDATE customer SET organizationId = 2 WHERE customerId = 4;
UPDATE customer SET organizationId = 1 WHERE customerId = 6;
UPDATE customer SET organizationId = 3 WHERE customerId = 7;

-- event (before reservation so eventId refs work)
INSERT INTO event VALUES (1, 'Acme Annual Conference', 1, 1, '2026-04-10 09:00:00', '2026-04-12 17:00:00', 200, 150, 'CONFIRMED');
INSERT INTO event VALUES (2, 'Global Events Gala Dinner', 4, 4, '2026-04-15 18:00:00', '2026-04-15 23:00:00', 80, 40, 'PLANNED');
INSERT INTO event VALUES (3, 'TechStart Product Launch', 7, 3, '2026-05-01 10:00:00', '2026-05-01 16:00:00', 50, 20, 'PLANNED');

-- reservation
INSERT INTO reservation VALUES (1, 1, 1, '2026-02-01', '2026-04-10', '2026-04-12', 1, 'CONFIRMED', 0, NULL, NULL);
INSERT INTO reservation VALUES (2, 2, NULL, '2026-03-01', '2026-04-20', '2026-04-23', 2, 'CONFIRMED', 1, 200, 1);
INSERT INTO reservation VALUES (3, 3, 3, '2026-03-15', '2026-05-01', '2026-05-02', 1, 'PENDING', 1, 150, 0);

-- reservation_preference
INSERT INTO reservation_preference VALUES (1, 1, 'BED_TYPE', 'KING');
INSERT INTO reservation_preference VALUES (2, 1, 'SMOKING', 'FALSE');
INSERT INTO reservation_preference VALUES (3, 2, 'POOL_PROXIMITY', 'TRUE');
INSERT INTO reservation_preference VALUES (4, 2, 'HANDICAPPED', 'FALSE');
INSERT INTO reservation_preference VALUES (5, 3, 'BED_TYPE', 'QUEEN');
INSERT INTO reservation_preference VALUES (6, 3, 'SMOKING', 'FALSE');

-- room_assignment
INSERT INTO room_assignment VALUES (1, 1, 1, 1, '2026-04-09', '2026-04-10 16:00:00', '2026-04-12 11:30:00', 0, NULL, NULL, 0);
INSERT INTO room_assignment VALUES (2, 2, 3, 2, '2026-04-18', '2026-04-20 15:45:00', NULL, 0, NULL, NULL, 1);
INSERT INTO room_assignment VALUES (3, 2, 1, 2, '2026-04-21', '2026-04-21 16:00:00', NULL, 0, NULL, NULL, 1);

-- time_slot
INSERT INTO time_slot VALUES (1, 'BREAKFAST', '07:00', '09:00', 1);
INSERT INTO time_slot VALUES (2, 'MORNING', '09:00', '12:00', 0);
INSERT INTO time_slot VALUES (3, 'LUNCH', '12:00', '14:00', 1);
INSERT INTO time_slot VALUES (4, 'AFTERNOON', '14:00', '17:00', 0);
INSERT INTO time_slot VALUES (5, 'SUPPER', '17:00', '19:00', 1);
INSERT INTO time_slot VALUES (6, 'EVENING', '19:00', '22:00', 0);
INSERT INTO time_slot VALUES (7, 'NIGHT', '22:00', '00:00', 0);

-- event_room
INSERT INTO event_room VALUES (1, 1, 2, 2, '2026-04-10', 0, 500, 0);
INSERT INTO event_room VALUES (2, 1, 2, 3, '2026-04-10', 1, 0, 0);
INSERT INTO event_room VALUES (3, 2, 2, 5, '2026-04-15', 0, 500, 0);

-- event_guest
INSERT INTO event_guest VALUES (1, 1, 'ORGANIZER');
INSERT INTO event_guest VALUES (1, 2, 'ATTENDEE');
INSERT INTO event_guest VALUES (2, 4, 'ORGANIZER');

-- charge
INSERT INTO charge VALUES (1, 1, 1, 'ROOM', 'Room 101, 2 nights at $250', 500, '2026-04-12 11:30:00', '2026-04-12 11:35:00', 'BILLED');
INSERT INTO charge VALUES (2, 1, 1, 'PHONE', 'Long distance call, 12 min', 15, '2026-04-11 09:20:00', '2026-04-11 09:25:00', 'BILLED');
INSERT INTO charge VALUES (3, 2, 2, 'ROOM', 'Room 102 Suite, 3 nights at $400', 1200, '2026-04-23 12:00:00', '2026-04-23 12:05:00', 'ACTUAL');

-- billing_split
INSERT INTO billing_split VALUES (1, 2, 2, 'ROOM_CHARGE', 50, NULL);
INSERT INTO billing_split VALUES (2, 2, 5, 'ROOM_CHARGE', 50, NULL);
INSERT INTO billing_split VALUES (3, 2, 2, 'PHONE', 100, NULL);

-- facility
INSERT INTO facility VALUES (1, 1, 'Ocean Grill Restaurant', 'RESTAURANT', 'Ocean Tower lobby level');
INSERT INTO facility VALUES (2, 1, 'Coral Health Club', 'HEALTH_CLUB', 'Palm Wing ground floor');
INSERT INTO facility VALUES (3, 1, 'Reef Business Center', 'BUSINESS_CENTER', 'Coral Building 2nd floor');

-- guest_card
INSERT INTO guest_card VALUES (1, 1, 4821, 'GUEST', '2026-04-10 15:50:00', 0);
INSERT INTO guest_card VALUES (2, 2, 7733, 'GUEST', '2026-04-20 15:40:00', 1);
INSERT INTO guest_card VALUES (3, NULL, 0000, 'STAFF_CLEANING', '2026-01-01 08:00:00', 1);

-- card_reader
INSERT INTO card_reader VALUES (1, 1, NULL, 'Room 101 door');
INSERT INTO card_reader VALUES (2, 2, NULL, 'Meeting Room 201 door');
INSERT INTO card_reader VALUES (3, NULL, 1, 'Ocean Grill entrance');

-- card_scan_log
INSERT INTO card_scan_log VALUES (1, 1, 1, '2026-04-10 16:00:00', 'ENTERING');
INSERT INTO card_scan_log VALUES (2, 1, 3, '2026-04-10 19:30:00', 'ENTERING');
INSERT INTO card_scan_log VALUES (3, 2, 1, '2026-04-20 15:45:00', 'ENTERING');

-- guest_message
INSERT INTO guest_message VALUES (1, 1, 'INCOMING_MESSAGE', 'Please call John at Acme re: conference schedule', 'John Smith', '305-555-9999', '2026-04-10 17:00:00', 0);
INSERT INTO guest_message VALUES (2, 2, 'OUTGOING_VOICEMAIL', 'I will be at the pool until 5pm', NULL, NULL, '2026-04-20 14:00:00', 1);
INSERT INTO guest_message VALUES (3, 3, 'STAFF_RELAY', 'Your car service confirmed for May 2 at 8am', 'Front Desk', NULL, '2026-04-28 10:00:00', 0);
