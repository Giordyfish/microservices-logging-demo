@echo off
REM Test script for microservices demo (Windows Batch)
REM This script generates sample traffic to demonstrate logging and tracing

setlocal enabledelayedexpansion

if "%API_URL%"=="" set API_URL=http://localhost:8000

echo ==========================================
echo Testing E-Commerce Microservices Demo
echo ==========================================
echo.

REM Test 1: Health check
echo [1] Health check
curl -s "%API_URL%/"
echo.
echo.

REM Test 2: Get all products
echo [2] Getting all products
curl -s "%API_URL%/products"
echo.
echo.

REM Test 3: Get specific product
echo [3] Getting product #1
curl -s "%API_URL%/products/1"
echo.
echo.

REM Test 4: Get product by category
echo [4] Getting Electronics products
curl -s "%API_URL%/products?category=Electronics"
echo.
echo.

REM Test 5: Create a valid order
echo [5] Creating a valid order
curl -s -X POST "%API_URL%/orders" ^
  -H "Content-Type: application/json" ^
  -d "{\"product_id\": 1, \"quantity\": 2, \"customer_name\": \"Alice Smith\", \"customer_email\": \"alice@example.com\"}"
echo.
echo.

REM Test 6: Create an invalid order (product doesn't exist)
echo [6] Attempting to create order with invalid product (should fail)
curl -s -X POST "%API_URL%/orders" ^
  -H "Content-Type: application/json" ^
  -d "{\"product_id\": 999, \"quantity\": 1, \"customer_name\": \"Bob Jones\", \"customer_email\": \"bob@example.com\"}"
echo.
echo.

REM Test 7: Get non-existent product (should fail)
echo [7] Attempting to get non-existent product (should fail)
curl -s "%API_URL%/products/999"
echo.
echo.

REM Test 8: Create multiple orders to generate traffic
echo [8] Creating multiple orders for demo purposes
for /L %%i in (1,1,5) do (
  set /a PRODUCT_ID=!RANDOM! %% 5 + 1
  set /a QUANTITY=!RANDOM! %% 3 + 1
  echo   Creating order for product #!PRODUCT_ID! (quantity: !QUANTITY!)
  curl -s -X POST "%API_URL%/orders" ^
    -H "Content-Type: application/json" ^
    -d "{\"product_id\": !PRODUCT_ID!, \"quantity\": !QUANTITY!, \"customer_name\": \"Customer %%i\", \"customer_email\": \"customer%%i@example.com\"}" > nul
)
echo.

echo ==========================================
echo Test completed successfully!
echo ==========================================
echo.
echo Now check Grafana to see the logs and traces:
echo   - Grafana: http://localhost:3000
echo   - Go to Explore -^> Loki to see logs
echo   - Go to Explore -^> Tempo to see traces
echo.

endlocal
