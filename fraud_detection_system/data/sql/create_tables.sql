CREATE TABLE
    IF NOT EXISTS customers (
        customer_id VARCHAR(50) PRIMARY KEY,
        customer_name VARCHAR(255) NOT NULL,
        email VARCHAR(255) UNIQUE NOT NULL,
        phone_number VARCHAR(50) UNIQUE NOT NULL,
        account_number VARCHAR(50) UNIQUE NOT NULL,
        date_of_birth DATE,
        gender VARCHAR(20),
        account_type VARCHAR(50),
        account_open_date DATE,
        account_age_days INTEGER,
        nationality VARCHAR(100),
        country VARCHAR(100),
        city VARCHAR(100),
        address TEXT,
        occupation VARCHAR(100),
        annual_income NUMERIC(15, 2),
        kyc_status VARCHAR(20),
        customer_risk_rating VARCHAR(20),
        previous_fraud_flag BOOLEAN DEFAULT FALSE,
        fraud_incident_count INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

CREATE TABLE
    IF NOT EXISTS devices (
        device_id VARCHAR(100) PRIMARY KEY,
        device_fingerprint VARCHAR(255) UNIQUE,
        device_type VARCHAR(50),
        operating_system VARCHAR(100),
        browser VARCHAR(100),
        first_seen TIMESTAMP,
        last_seen TIMESTAMP,
        device_risk_score NUMERIC(5, 2),
        is_blacklisted BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

CREATE TABLE
    IF NOT EXISTS beneficiaries (
        beneficiary_id VARCHAR(50) PRIMARY KEY,
        receiver_account VARCHAR(50) UNIQUE NOT NULL,
        receiver_name VARCHAR(255),
        bank_name VARCHAR(255),
        country VARCHAR(100),
        risk_rating VARCHAR(20),
        fraud_link_count INTEGER DEFAULT 0,
        sanction_match_flag BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

CREATE TABLE
    IF NOT EXISTS merchants (
        merchant_id VARCHAR(50) PRIMARY KEY,
        merchant_name VARCHAR(255) UNIQUE NOT NULL,
        merchant_category VARCHAR(100),
        merchant_country VARCHAR(100),
        merchant_risk_rating VARCHAR(20),
        fraud_transaction_count INTEGER DEFAULT 0,
        total_transaction_count INTEGER DEFAULT 0,
        merchant_status VARCHAR(50),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

CREATE TABLE
    IF NOT EXISTS customer_devices (
        customer_device_id VARCHAR(50) PRIMARY KEY,
        customer_id VARCHAR(50) NOT NULL,
        device_id VARCHAR(100) NOT NULL,
        first_seen TIMESTAMP,
        last_seen TIMESTAMP,
        FOREIGN KEY (customer_id) REFERENCES customers (customer_id) ON DELETE CASCADE,
        FOREIGN KEY (device_id) REFERENCES devices (device_id) ON DELETE CASCADE,
        CONSTRAINT unique_customer_device UNIQUE (customer_id, device_id)
    );

CREATE TABLE
    IF NOT EXISTS customer_beneficiaries (
        customer_beneficiary_id VARCHAR(50) PRIMARY KEY,
        customer_id VARCHAR(50) NOT NULL,
        beneficiary_id VARCHAR(50) NOT NULL,
        first_transaction_date TIMESTAMP,
        last_transaction_date TIMESTAMP,
        relationship_risk_score NUMERIC(5, 2),
        FOREIGN KEY (customer_id) REFERENCES customers (customer_id) ON DELETE CASCADE,
        FOREIGN KEY (beneficiary_id) REFERENCES beneficiaries (beneficiary_id) ON DELETE CASCADE,
        CONSTRAINT unique_customer_beneficiary UNIQUE (customer_id, beneficiary_id)
    );

CREATE TABLE
    IF NOT EXISTS sanction_list (
        entity_id VARCHAR(50) PRIMARY KEY,
        entity_name VARCHAR(255),
        entity_type VARCHAR(50),
        country VARCHAR(100),
        sanction_source VARCHAR(100),
        sanction_category VARCHAR(100),
        reason_for_sanction TEXT,
        risk_level VARCHAR(20),
        pep_flag BOOLEAN,
        fraudster_flag BOOLEAN,
        blacklist_flag BOOLEAN,
        regulatory_reference TEXT,
        effective_date DATE,
        expiry_date DATE,
        status VARCHAR(50),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

CREATE TABLE
    IF NOT EXISTS transactions (
        transaction_id VARCHAR(50) PRIMARY KEY,
        customer_id VARCHAR(50) NOT NULL,
        beneficiary_id VARCHAR(50),
        merchant_id VARCHAR(50),
        device_id VARCHAR(100),
        transaction_timestamp TIMESTAMP NOT NULL,
        transaction_type VARCHAR(50),
        transaction_amount NUMERIC(15, 2),
        currency CHAR(3),
        payment_method VARCHAR(50),
        transaction_status VARCHAR(20),
        ip_address VARCHAR(100),
        origin_country VARCHAR(100),
        destination_country VARCHAR(100),
        is_international BOOLEAN,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (customer_id) REFERENCES customers (customer_id) ON DELETE RESTRICT,
        FOREIGN KEY (beneficiary_id) REFERENCES beneficiaries (beneficiary_id) ON DELETE SET NULL,
        FOREIGN KEY (merchant_id) REFERENCES merchants (merchant_id) ON DELETE SET NULL,
        FOREIGN KEY (device_id) REFERENCES devices (device_id) ON DELETE SET NULL
    );

CREATE TABLE
    IF NOT EXISTS customer_behavior (
        behavior_id VARCHAR(50) PRIMARY KEY,
        customer_id VARCHAR(50) NOT NULL,
        transaction_id VARCHAR(50) UNIQUE,
        device_id VARCHAR(100),
        login_timestamp TIMESTAMP,
        logout_timestamp TIMESTAMP,
        session_duration_minutes INTEGER,
        behavior_risk_score NUMERIC(5, 2),
        account_takeover_suspected BOOLEAN,
        transaction_frequency_24h INTEGER,
        avg_transaction_amount_7d NUMERIC(15, 2),
        failed_transaction_count_24h INTEGER,
        unusual_amount_flag BOOLEAN,
        unusual_location_flag BOOLEAN,
        typing_speed_flag BOOLEAN,
        fraud_flag BOOLEAN,
        fraud_risk VARCHAR(20),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (customer_id) REFERENCES customers (customer_id) ON DELETE CASCADE,
        FOREIGN KEY (transaction_id) REFERENCES transactions (transaction_id) ON DELETE SET NULL,
        FOREIGN KEY (device_id) REFERENCES devices (device_id) ON DELETE SET NULL
    );

CREATE TABLE
    IF NOT EXISTS transaction_analysis_logs (
        transaction_analysis_id VARCHAR(50) PRIMARY KEY,
        transaction_id VARCHAR(50) NOT NULL UNIQUE,
        customer_id VARCHAR(50) NOT NULL,
        fraud_probability NUMERIC(5, 2),
        behavior_score NUMERIC(5, 2),
        graph_score NUMERIC(5, 2),
        sanction_score NUMERIC(5, 2),
        overall_risk_score NUMERIC(5, 2),
        risk_category VARCHAR(20),
        decision VARCHAR(50),
        agent1_output JSONB,
        agent2_output JSONB,
        agent3_output JSONB,
        agent4_output JSONB,
        agent5_output JSONB,
        recommended_action TEXT,
        investigation_status VARCHAR(50),
        report BYTEA,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (transaction_id) REFERENCES transactions (transaction_id) ON DELETE CASCADE,
        FOREIGN KEY (customer_id) REFERENCES customers (customer_id) ON DELETE CASCADE
    );

-- Performance optimization for critical relational joins
CREATE INDEX idx_transactions_customer_id ON transactions (customer_id);

CREATE INDEX idx_transactions_beneficiary_id ON transactions (beneficiary_id);

CREATE INDEX idx_transactions_merchant_id ON transactions (merchant_id);

CREATE INDEX idx_transactions_device_id ON transactions (device_id);

CREATE INDEX idx_customer_behavior_customer_id ON customer_behavior (customer_id);

CREATE INDEX idx_analysis_logs_transaction_id ON transaction_analysis_logs (transaction_id);