-- ═══════════════════════════════════════════════════════════════════════════
-- analytics_queries.sql
-- Sample BI queries for Power BI using the insurance_db Star Schema.
-- Run in: insurance_db
-- ═══════════════════════════════════════════════════════════════════════════


-- ── 1. Portfolio summary ───────────────────────────────────────────────────
SELECT * FROM vw_portfolio_kpis;


-- ── 2. Policy volume by year ───────────────────────────────────────────────
SELECT
    d.year,
    COUNT(*)                                                                AS policy_count,
    ROUND(SUM(fp.premium)::NUMERIC, 2)                                      AS total_premium,
    ROUND(SUM(fp.claim_paid)::NUMERIC, 2)                                   AS total_claim_paid,
    ROUND((SUM(fp.claim_paid) / NULLIF(SUM(fp.premium), 0))::NUMERIC, 4)    AS loss_ratio
FROM fact_policies fp
JOIN dim_date d ON fp.insr_begin_id = d.date_id
GROUP BY d.year
ORDER BY d.year;


-- ── 3. Top 15 vehicle makes by policy count ────────────────────────────────
SELECT
    v.make,
    COUNT(*)                                                                AS policy_count,
    ROUND(AVG(fp.premium)::NUMERIC, 2)                                      AS avg_premium,
    ROUND((SUM(fp.claim_paid) / NULLIF(SUM(fp.premium), 0))::NUMERIC, 4)    AS loss_ratio,
    ROUND(AVG(fp.risk_score)::NUMERIC, 2)                                   AS avg_risk_score
FROM fact_policies fp
JOIN dim_vehicle v ON fp.vehicle_id = v.vehicle_id
GROUP BY v.make
ORDER BY policy_count DESC
LIMIT 15;


-- ── 4. KPIs by insurance product type ─────────────────────────────────────
SELECT * FROM vw_product_kpis;


-- ── 5. Renewal candidates by vehicle make ─────────────────────────────────
SELECT
    v.make,
    COUNT(*)                                AS renewal_candidates,
    ROUND(AVG(fp.premium)::NUMERIC, 2)      AS avg_premium,
    ROUND(AVG(fp.risk_score)::NUMERIC, 2)   AS avg_risk_score
FROM fact_policies fp
JOIN dim_vehicle v ON fp.vehicle_id = v.vehicle_id
WHERE fp.renewal_candidate = TRUE
GROUP BY v.make
ORDER BY renewal_candidates DESC
LIMIT 15;


-- ── 6. Risk score distribution ────────────────────────────────────────────
SELECT
    risk_score,
    COUNT(*)                                                AS policy_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2)      AS pct
FROM fact_policies
GROUP BY risk_score
ORDER BY risk_score;


-- ── 7. Premium segment breakdown by insurance type ────────────────────────
SELECT
    i.insr_type_name,
    fp.premium_segment,
    COUNT(*)                                AS policy_count,
    ROUND(AVG(fp.premium)::NUMERIC, 2)      AS avg_premium
FROM fact_policies fp
JOIN dim_insurance_type i ON fp.insurance_type_id = i.insurance_type_id
GROUP BY i.insr_type_name, fp.premium_segment
ORDER BY i.insr_type_name, fp.premium_segment;


-- ── 8. Monthly new policy trend ───────────────────────────────────────────
SELECT
    d.year,
    d.month,
    d.month_name,
    COUNT(*)                                AS new_policies,
    ROUND(SUM(fp.premium)::NUMERIC, 2)      AS total_premium
FROM fact_policies fp
JOIN dim_date d ON fp.insr_begin_id = d.date_id
GROUP BY d.year, d.month, d.month_name
ORDER BY d.year, d.month;


-- ── 9. High-risk policies by vehicle type ─────────────────────────────────
SELECT
    v.type_vehicle,
    COUNT(*)                                                                        AS policy_count,
    SUM(CASE WHEN fp.risk_score >= 2 THEN 1 ELSE 0 END)                            AS high_risk_count,
    ROUND(100.0 * SUM(CASE WHEN fp.risk_score >= 2 THEN 1 ELSE 0 END) / COUNT(*), 2) AS high_risk_pct,
    ROUND(AVG(fp.risk_score)::NUMERIC, 2)                                           AS avg_risk_score
FROM fact_policies fp
JOIN dim_vehicle v ON fp.vehicle_id = v.vehicle_id
GROUP BY v.type_vehicle
ORDER BY high_risk_pct DESC;


-- ── 10. Claim rate analysis ────────────────────────────────────────────────
SELECT
    CASE WHEN fp.claim_paid > 0 THEN 'With Claim' ELSE 'No Claim' END  AS claim_status,
    COUNT(*)                                                            AS policy_count,
    ROUND(AVG(fp.premium)::NUMERIC, 2)                                  AS avg_premium,
    ROUND(AVG(fp.claim_paid)::NUMERIC, 2)                               AS avg_claim_paid,
    ROUND(AVG(fp.risk_score)::NUMERIC, 2)                               AS avg_risk_score
FROM fact_policies fp
GROUP BY claim_status
ORDER BY claim_status;