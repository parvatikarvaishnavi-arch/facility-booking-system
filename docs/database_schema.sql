CREATE TABLE booking_facility (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
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
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    facility_id BIGINT NOT NULL,
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
    CONSTRAINT booking_facility_fk FOREIGN KEY (facility_id) REFERENCES booking_facility(id),
    CONSTRAINT booking_end_after_start CHECK (end_time > start_time)
);

CREATE INDEX booking_facility_date_status_idx
    ON booking_booking (facility_id, booking_date, status);

CREATE INDEX booking_customer_date_idx
    ON booking_booking (customer_email, booking_date);

CREATE TABLE booking_complimentarylounge (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    customer_email VARCHAR(254) NOT NULL UNIQUE,
    customer_name VARCHAR(120) NOT NULL,
    free_booking_used BOOLEAN NOT NULL DEFAULT FALSE,
    booking_id BIGINT NULL UNIQUE,
    used_at DATETIME(6) NULL,
    created_at DATETIME(6) NOT NULL,
    CONSTRAINT complimentary_lounge_booking_fk
        FOREIGN KEY (booking_id) REFERENCES booking_booking(id)
        ON DELETE SET NULL
);

