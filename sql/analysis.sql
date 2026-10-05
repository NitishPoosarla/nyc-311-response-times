-- 02-operations-311 — reproduce ops metrics in SQL (BigQuery dialect where noted).
-- Loads: data/processed/cases_clean.csv -> table `cases` (created_date TIMESTAMP, resolve_h FLOAT).

-- Quarter KPIs: backlog, median/P90 resolution (APPROX_QUANTILES = BigQuery)
SELECT
  COUNT(*) AS cases,
  ROUND(AVG(open) * 100, 1) AS backlog_pct,
  APPROX_QUANTILES(resolve_h, 100)[OFFSET(50)] AS median_resolve_h,
  APPROX_QUANTILES(resolve_h, 100)[OFFSET(90)] AS p90_resolve_h
FROM cases;

-- Slowest heavy-volume agencies (SQLite version: ORDER BY BAR uses p50 via window)
SELECT agency_name, COUNT(*) AS cases, resolve_h AS med_h
FROM (SELECT agency_name, resolve_h,
             PERCENT_RANK() OVER (PARTITION BY agency_name ORDER BY resolve_h) pr
      FROM cases WHERE open = 0)
WHERE pr = 0.5
GROUP BY agency_name, resolve_h
ORDER BY resolve_h DESC;

-- >72h SLA-miss share among closed cases
SELECT ROUND(100.0 * SUM(resolve_h > 72) / COUNT(*), 1) AS over_72h_pct
FROM cases WHERE open = 0;

-- Arrival hour heat (bi-hourly bins)
SELECT CAST(EXTRACT(HOUR FROM created_date) / 4 AS INT64) AS arrival_block_6h,
       COUNT(*) AS complaints
FROM cases GROUP BY 1 ORDER BY 1;
