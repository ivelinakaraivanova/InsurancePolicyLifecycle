-- SELECT current_database();
-- SELECT * FROM policies_lifecycle LIMIT 10;
-- SELECT DISTINCT insr_type FROM policies_lifecycle pl;
-- SELECT DISTINCT pl.type_vehicle FROM policies_lifecycle pl;

-- SELECT MAX(insr_end) FROM policies_lifecycle;

-- SELECT DISTINCT effective_yr FROM policies_lifecycle 
-- WHERE effective_yr !~ '^\d+$';

-- ═══════════════════════════════════════════════════════════════════════════
-- create_star_schema.sql
-- Prerequisites: gold_to_postgres.py must have loaded policies_lifecycle.
-- Run in: insurance_db
-- ═══════════════════════════════════════════════════════════════════════════


DROP TABLE IF EXISTS fact_policies;
DROP TABLE IF EXISTS dim_vehicle;
DROP TABLE IF EXISTS dim_insurance_type;
DROP TABLE IF EXISTS dim_date CASCADE;


-- ── dim_vehicle ─────────────────────────────────────────────────────────
CREATE TABLE dim_vehicle AS
SELECT
    ROW_NUMBER() OVER (ORDER BY make, type_vehicle, ccm_ton, seats_num)::INTEGER AS vehicle_id,
    make,
    type_vehicle,
    ccm_ton,
    seats_num::INTEGER      AS seats_num,
    carrying_capacity,
    usage
FROM (
    SELECT DISTINCT make, type_vehicle, ccm_ton, seats_num, carrying_capacity, usage
    FROM policies_lifecycle
) t;

ALTER TABLE dim_vehicle ADD PRIMARY KEY (vehicle_id);

SELECT * FROM dim_vehicle dv LIMIT 15;

-- ── dim_insurance_type ──────────────────────────────────────────────────
CREATE TABLE dim_insurance_type AS
SELECT
    ROW_NUMBER() OVER (ORDER BY insr_type)::INTEGER AS insurance_type_id,
    insr_type AS insr_type_code,
    CASE insr_type
    	WHEN 1201 THEN 'Third party'
    	WHEN 1202 THEN 'Comprehensive'
    	WHEN 1204 THEN 'Other'
    	ELSE 'Unknown'
    END AS insr_type_name
FROM (
    SELECT DISTINCT insr_type FROM policies_lifecycle
) t;

ALTER TABLE dim_insurance_type ADD PRIMARY KEY (insurance_type_id);

SELECT * FROM dim_insurance_type dit LIMIT 15;

-- ── dim_date ────────────────────────────────────────────────────────────
CREATE TABLE dim_date AS
SELECT
    TO_CHAR(d, 'YYYYMMDD')::INTEGER      AS date_id,
    d::DATE                              AS full_date,
    EXTRACT(YEAR    FROM d)::SMALLINT    AS year,
    EXTRACT(QUARTER FROM d)::SMALLINT    AS quarter,
    EXTRACT(MONTH   FROM d)::SMALLINT    AS month,
    TRIM(TO_CHAR(d, 'Month'))            AS month_name,
    EXTRACT(DAY     FROM d)::SMALLINT    AS day,
    EXTRACT(DOW     FROM d)::SMALLINT    AS day_of_week,
    TRIM(TO_CHAR(d, 'Day'))              AS day_name,
    (EXTRACT(DOW FROM d) IN (0, 6))      AS is_weekend
FROM GENERATE_SERIES(
    '2011-01-01'::DATE,
    '2020-12-31'::DATE,
    '1 day'::INTERVAL
) AS d;

ALTER TABLE dim_date ADD PRIMARY KEY (date_id);

SELECT * FROM dim_date dd LIMIT 15;

-- ── fact_policies ───────────────────────────────────────────────
CREATE TABLE fact_policies AS
SELECT
    ROW_NUMBER() OVER ()::BIGINT                    AS fact_id,
    p.object_id::BIGINT                             AS object_id,
    v.vehicle_id,
    i.insurance_type_id,
    TO_CHAR(p.insr_begin, 'YYYYMMDD')::INTEGER      AS insr_begin_id,
    TO_CHAR(p.insr_end,   'YYYYMMDD')::INTEGER      AS insr_end_id,
    p.prod_year::SMALLINT                           AS prod_year,
    p.sex::SMALLINT                                 AS sex,
    p.insured_value,
    p.premium,
    p.claim_paid,
    p.policy_duration_days::INTEGER                 AS policy_duration_days,
    p.vehicle_age::SMALLINT                         AS vehicle_age,
    p.premium_segment,
    p.value_segment,
    p.lifecycle_status,
    p.is_active,
    p.is_expired,
    p.renewal_candidate,
    p.risk_score::SMALLINT                          AS risk_score
FROM policies_lifecycle p
JOIN dim_vehicle v
    ON  p.make              IS NOT DISTINCT FROM v.make
    AND p.type_vehicle      IS NOT DISTINCT FROM v.type_vehicle
    AND p.ccm_ton           IS NOT DISTINCT FROM v.ccm_ton
    AND p.seats_num::INTEGER IS NOT DISTINCT FROM v.seats_num
    AND p.carrying_capacity IS NOT DISTINCT FROM v.carrying_capacity
    AND p.usage             IS NOT DISTINCT FROM v.usage
JOIN dim_insurance_type i
    ON p.insr_type = i.insr_type_code;

ALTER TABLE fact_policies ADD PRIMARY KEY (fact_id);
ALTER TABLE fact_policies ADD FOREIGN KEY (vehicle_id)        REFERENCES dim_vehicle(vehicle_id);
ALTER TABLE fact_policies ADD FOREIGN KEY (insurance_type_id) REFERENCES dim_insurance_type(insurance_type_id);
ALTER TABLE fact_policies ADD FOREIGN KEY (insr_begin_id)     REFERENCES dim_date(date_id);
ALTER TABLE fact_policies ADD FOREIGN KEY (insr_end_id)       REFERENCES dim_date(date_id);

SELECT * FROM fact_policies fp LIMIT 15;
