-- ═══════════════════════════════════════════════════════════════════════════
-- create_kpi_views.sql
-- KPI views over the Star Schema for the Insurance Policy Lifecycle pipeline.
-- Prerequisites: create_star_schema_ins.sql must have been run.
-- Run in: insurance_db
-- ═══════════════════════════════════════════════════════════════════════════


-- ── portfolio_kpis_view ────────────────────────────────────────────────────
CREATE OR REPLACE VIEW vw_portfolio_kpis AS
SELECT
    COUNT(*)                                                            AS policy_count,
    SUM(is_active::INT)                                                 AS active_count,
    SUM(is_expired::INT)                                                AS expired_count,
    SUM(CASE WHEN lifecycle_status = 'future' THEN 1 ELSE 0 END)        AS future_count,
    SUM(renewal_candidate::INT)                                         AS renewal_candidate_count,
    ROUND(SUM(premium)::NUMERIC, 2)                                     AS total_premium,
    ROUND(AVG(premium)::NUMERIC, 2)                                     AS avg_premium,
    ROUND(SUM(claim_paid)::NUMERIC, 2)                                  AS total_claim_paid,
    ROUND(AVG(claim_paid)::NUMERIC, 2)                                  AS avg_claim_paid,
    ROUND((SUM(claim_paid) / NULLIF(SUM(premium), 0))::NUMERIC, 4)      AS loss_ratio,
    ROUND(AVG(policy_duration_days)::NUMERIC, 1)                        AS avg_policy_duration_days,
    ROUND(AVG(risk_score)::NUMERIC, 2)                                  AS avg_risk_score,
    SUM(CASE WHEN risk_score >= 2 THEN 1 ELSE 0 END)                    AS high_risk_count
FROM fact_policies;

SELECT * FROM vw_portfolio_kpis;


-- ── vehicle_kpis_view ──────────────────────────────────────────────────────
CREATE OR REPLACE VIEW vw_vehicle_kpis AS
SELECT
    v.make,
    v.type_vehicle,
    COUNT(*)                                                           AS policy_count,
    SUM(fp.is_active::INT)                                             AS active_count,
    ROUND(AVG(fp.vehicle_age)::NUMERIC, 1)                             AS avg_vehicle_age,
    ROUND(SUM(fp.premium)::NUMERIC, 2)                                 AS total_premium,
    ROUND(AVG(fp.premium)::NUMERIC, 2)                                 AS avg_premium,
    ROUND(SUM(fp.claim_paid)::NUMERIC, 2)                              AS total_claim_paid,
    ROUND(AVG(fp.claim_paid)::NUMERIC, 2)                              AS avg_claim_paid,
    ROUND((SUM(fp.claim_paid) / NULLIF(SUM(fp.premium), 0))::NUMERIC, 4) AS loss_ratio,
    ROUND(AVG(fp.risk_score)::NUMERIC, 2)                              AS avg_risk_score
FROM fact_policies fp
JOIN dim_vehicle v ON fp.vehicle_id = v.vehicle_id
GROUP BY v.make, v.type_vehicle
ORDER BY policy_count DESC;

SELECT * FROM vw_vehicle_kpis LIMIT 15;


-- ── product_kpis_view ──────────────────────────────────────────────────────
CREATE OR REPLACE VIEW vw_product_kpis AS
SELECT
    i.insr_type_name,
    COUNT(*)                                                           AS policy_count,
    SUM(fp.is_active::INT)                                             AS active_count,
    SUM(fp.is_expired::INT)                                            AS expired_count,
    SUM(fp.renewal_candidate::INT)                                     AS renewal_candidate_count,
    ROUND(SUM(fp.premium)::NUMERIC, 2)                                 AS total_premium,
    ROUND(AVG(fp.premium)::NUMERIC, 2)                                 AS avg_premium,
    ROUND(SUM(fp.claim_paid)::NUMERIC, 2)                              AS total_claim_paid,
    ROUND(AVG(fp.claim_paid)::NUMERIC, 2)                              AS avg_claim_paid,
    ROUND((SUM(fp.claim_paid) / NULLIF(SUM(fp.premium), 0))::NUMERIC, 4) AS loss_ratio,
    ROUND(AVG(fp.policy_duration_days)::NUMERIC, 1)                    AS avg_policy_duration_days,
    SUM(CASE WHEN fp.premium_segment = 'low'    THEN 1 ELSE 0 END)     AS premium_seg_low,
    SUM(CASE WHEN fp.premium_segment = 'medium' THEN 1 ELSE 0 END)     AS premium_seg_medium,
    SUM(CASE WHEN fp.premium_segment = 'high'   THEN 1 ELSE 0 END)     AS premium_seg_high
FROM fact_policies fp
JOIN dim_insurance_type i ON fp.insurance_type_id = i.insurance_type_id
GROUP BY i.insr_type_name
ORDER BY policy_count DESC;

SELECT * FROM vw_product_kpis LIMIT 15;