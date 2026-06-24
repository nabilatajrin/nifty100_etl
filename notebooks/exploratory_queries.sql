-- ============================================================
-- exploratory_queries.sql — Sprint 1, Day 7
-- 10 exploratory queries for nifty100.db
-- Run interactively:  sqlite3 data/nifty100.db < notebooks/exploratory_queries.sql
-- ============================================================

-- Q1. Row counts for every core table
SELECT 'companies'        AS table_name, COUNT(*) AS rows FROM companies
UNION ALL SELECT 'profitandloss',    COUNT(*) FROM profitandloss
UNION ALL SELECT 'balancesheet',     COUNT(*) FROM balancesheet
UNION ALL SELECT 'cashflow',         COUNT(*) FROM cashflow
UNION ALL SELECT 'financial_ratios', COUNT(*) FROM financial_ratios
UNION ALL SELECT 'market_cap',       COUNT(*) FROM market_cap
UNION ALL SELECT 'stock_prices',     COUNT(*) FROM stock_prices
UNION ALL SELECT 'sectors',          COUNT(*) FROM sectors;

-- Q2. Year coverage per company (P&L) — how many years each company has
SELECT company_id, COUNT(*) AS pl_years
FROM profitandloss
GROUP BY company_id
ORDER BY pl_years DESC;

-- Q3. Companies with fewer than 5 years of P&L history (DQ-16 flag)
SELECT company_id, COUNT(*) AS years
FROM profitandloss
GROUP BY company_id
HAVING years < 5
ORDER BY years;

-- Q4. Null check — how many P&L rows have missing net_profit or eps
SELECT
    SUM(CASE WHEN net_profit IS NULL THEN 1 ELSE 0 END) AS null_net_profit,
    SUM(CASE WHEN eps        IS NULL THEN 1 ELSE 0 END) AS null_eps,
    COUNT(*)                                            AS total_rows
FROM profitandloss;

-- Q5. Company count per broad sector
SELECT s.broad_sector, COUNT(*) AS num_companies
FROM sectors s
GROUP BY s.broad_sector
ORDER BY num_companies DESC;

-- Q6. Latest-year sales leaders — top 10 companies by most recent sales
SELECT p.company_id, c.company_name, p.year, p.sales
FROM profitandloss p
JOIN companies c ON c.id = p.company_id
WHERE p.year = (SELECT MAX(year) FROM profitandloss p2 WHERE p2.company_id = p.company_id)
ORDER BY p.sales DESC
LIMIT 10;

-- Q7. Min / max year present in the P&L table (data span)
SELECT MIN(year) AS earliest_year, MAX(year) AS latest_year
FROM profitandloss;

-- Q8. Debt-free companies in the latest year (borrowings = 0)
SELECT b.company_id, b.year, b.borrowings
FROM balancesheet b
WHERE b.borrowings = 0
  AND b.year = (SELECT MAX(year) FROM balancesheet b2 WHERE b2.company_id = b.company_id)
ORDER BY b.company_id;

-- Q9. Average operating profit margin by sector (latest year)
SELECT s.broad_sector,
       ROUND(AVG(p.opm_percentage), 2) AS avg_opm
FROM profitandloss p
JOIN sectors s ON s.company_id = p.company_id
WHERE p.year = (SELECT MAX(year) FROM profitandloss p2 WHERE p2.company_id = p.company_id)
GROUP BY s.broad_sector
ORDER BY avg_opm DESC;

-- Q10. Referential integrity spot-check — any P&L company_id missing from companies?
SELECT DISTINCT p.company_id
FROM profitandloss p
LEFT JOIN companies c ON c.id = p.company_id
WHERE c.id IS NULL;
