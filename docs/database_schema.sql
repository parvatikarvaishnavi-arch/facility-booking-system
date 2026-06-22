CREATE TABLE booking_facility (
    id CHAR(32) NOT NULL PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    slug VARCHAR(140) NOT NULL,
    facility_type VARCHAR(20) NOT NULL,
    member_charge DECIMAL(10, 2) NOT NULL,
    non_member_charge DECIMAL(10, 2) NOT NULL,
    operating_start TIME NOT NULL,
    operating_end TIME NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME(6) NOT NULL,
    CONSTRAINT unique_facility_type_slug UNIQUE (facility_type, slug),
    CONSTRAINT facility_operating_end_after_start CHECK (operating_end > operating_start)
);

CREATE TABLE booking_booking (
    id CHAR(32) NOT NULL PRIMARY KEY,
    facility_id CHAR(32) NOT NULL,
    customer_name VARCHAR(120) NOT NULL,
    customer_email VARCHAR(254) NOT NULL,
    booking_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    is_member BOOLEAN NOT NULL DEFAULT FALSE,
    total_charge DECIMAL(10, 2) NOT NULL DEFAULT 0,
    is_complimentary BOOLEAN NOT NULL DEFAULT FALSE,
    status VARCHAR(20) NOT NULL DEFAULT 'confirmed',
    created_at DATETIME(6) NOT NULL,
    updated_at DATETIME(6) NOT NULL,
    CONSTRAINT booking_facility_fk FOREIGN KEY (facility_id) REFERENCES booking_facility(id) ON DELETE RESTRICT,
    CONSTRAINT booking_end_after_start CHECK (end_time > start_time)
);

CREATE INDEX booking_boo_facilit_1dc6bd_idx
    ON booking_booking (facility_id, booking_date, status);

CREATE INDEX booking_boo_custome_954457_idx
    ON booking_booking (customer_email, booking_date);

