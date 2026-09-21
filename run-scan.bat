@echo off
echo Running the morning scan against your watchlist + broader market...
echo This checks 100+ tickers with rate-limited API calls, so it can take 2-3 minutes.
echo Do not close this window until it finishes.
echo.

curl -s -X POST http://localhost:8000/api/scan/run

echo.
echo.
echo Done. Check the dashboard tabs at http://localhost:5173 for results.
pause
