-- =====================================================
-- myIoT Platform Schema (TimescaleDB Optimized)
-- =====================================================

-- 🧩 Enable required extensions
CREATE EXTENSION IF NOT EXISTS timescaledb;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- =====================================================
-- ORGANISATION → SITE → PLANT → DEVICE
-- =====================================================

CREATE TABLE organisation_master (
    org_id        TEXT PRIMARY KEY,
    org_name      TEXT NOT NULL,
    contact_email TEXT,
    created_at    TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE site_master (
    site_id   TEXT PRIMARY KEY,
    org_id    TEXT REFERENCES organisation_master(org_id) ON DELETE CASCADE,
    site_name TEXT NOT NULL,
    location  TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE plant_master (
    plant_id   TEXT PRIMARY KEY,
    site_id    TEXT REFERENCES site_master(site_id) ON DELETE CASCADE,
    plant_name TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE device_master (
    device_id   TEXT PRIMARY KEY,
    plant_id    TEXT REFERENCES plant_master(plant_id) ON DELETE CASCADE,
    device_name TEXT,
    device_type TEXT,          -- e.g. 'energy_meter', 'air_sensor'
    model       TEXT,
    serial_no   TEXT,
    status      TEXT DEFAULT 'active',
    installed_at TIMESTAMPTZ,
    created_at   TIMESTAMPTZ DEFAULT now()
);

-- =====================================================
-- UNIFIED TELEMETRY TABLE (FOR ALL DEVICES)
-- =====================================================

CREATE TABLE telemetry (
    device_id TEXT REFERENCES device_master(device_id) ON DELETE CASCADE,
    ts TIMESTAMPTZ NOT NULL,
    data JSONB NOT NULL,  -- holds all key-value parameters
    inserted_at TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (device_id, ts)
);

-- Convert to hypertable (1-week chunks)
SELECT create_hypertable('telemetry', 'ts', chunk_time_interval => INTERVAL '7 days', if_not_exists => TRUE);

-- =====================================================
-- PERFORMANCE INDEX + COMPRESSION
-- =====================================================

-- Useful for queries like: WHERE device_id='em-001' AND ts BETWEEN ...
CREATE INDEX IF NOT EXISTS idx_telemetry_device_ts ON telemetry (device_id, ts DESC);

-- Enable compression and set policy
ALTER TABLE telemetry
  SET (
    timescaledb.compress,
    timescaledb.compress_orderby = 'ts DESC',
    timescaledb.compress_segmentby = 'device_id'
  );

-- Compress data older than 30 days
SELECT add_compression_policy('telemetry', INTERVAL '30 days');

-- =====================================================
-- EXAMPLE HIERARCHY SEED DATA
-- =====================================================

INSERT INTO organisation_master (org_id, org_name)
VALUES ('acme', 'Acme Industries')
ON CONFLICT DO NOTHING;

INSERT INTO site_master (site_id, org_id, site_name, location)
VALUES ('chd', 'acme', 'Chandigarh Site', 'Chandigarh, IN')
ON CONFLICT DO NOTHING;

INSERT INTO plant_master (plant_id, site_id, plant_name)
VALUES ('p7', 'chd', 'Plant 7')
ON CONFLICT DO NOTHING;

INSERT INTO device_master (device_id, plant_id, device_name, device_type, model)
VALUES ('em-001', 'p7', 'Energy Meter 001', 'energy_meter', 'EM6400NG+')
ON CONFLICT DO NOTHING;

-- =====================================================
-- SAMPLE TELEMETRY DATA (for validation)
-- =====================================================

INSERT INTO telemetry (device_id, ts, data)
VALUES (
  'em-001',
  now(),
  jsonb_build_object(
    'voltage_ll_avg', 430.2,
    'current_avg', 5.3,
    'frequency', 50.1,
    'pf_total', 0.96,
    'active_power_total', 2.4,
    'thd_v_r', 1.2,
    'energy_kwh', 12500.7
  )
);

-- List all tables in your DB
SELECT table_schema, table_name
FROM information_schema.tables
WHERE table_schema = 'public';



-- Disable compression (keeps existing chunks as-is)
ALTER TABLE telemetry SET (timescaledb.compress = false);

-- Decompress all chunks (takes time depending on size)
SELECT decompress_chunk(chunk_name) FROM show_chunks('telemetry');

-- Now do your ALTER or RLS
ALTER TABLE telemetry DISABLE ROW LEVEL SECURITY;

-- Re-enable compression policy
ALTER TABLE telemetry SET (timescaledb.compress = true);

CREATE POLICY org_isolation ON telemetry
USING (device_id IN (
    SELECT d.device_id
    FROM device_master d
    JOIN plant_master p ON d.plant_id = p.plant_id
    JOIN site_master s ON p.site_id = s.site_id
    JOIN organisation_master o ON s.org_id = o.org_id
    WHERE o.org_id = current_setting('app.current_org_id')
));







-- Verify hypertable creation


SELECT hypertable_name, count(chunk_name)
FROM timescaledb_information.chunks
GROUP BY hypertable_name;

SELECT hypertable_name
FROM timescaledb_information.hypertables;

SELECT
    j.hypertable_name,
    j.job_id,
    j.proc_name,
    j.scheduled,
    j.config
FROM timescaledb_information.jobs j
ORDER BY j.hypertable_name;


SELECT job_id, hypertable_name, proc_name, scheduled, next_start
FROM timescaledb_information.jobs
WHERE hypertable_name = 'telemetry';


