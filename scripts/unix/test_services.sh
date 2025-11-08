#!/bin/bash
# Test script for microservices demo
# This script generates sample traffic to demonstrate logging and tracing

set -e

API_URL="${API_URL:-http://localhost:8000}"

echo "=========================================="
echo "Testing E-Commerce Microservices Demo"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test 1: Health check
echo -e "${BLUE}[1] Health check${NC}"
curl -s "$API_URL/" | jq .
echo ""

# Test 2: Get all products
echo -e "${BLUE}[2] Getting all products${NC}"
curl -s "$API_URL/products" | jq .
echo ""

# Test 3: Get specific product
echo -e "${BLUE}[3] Getting product #1${NC}"
curl -s "$API_URL/products/1" | jq .
echo ""

# Test 4: Get product by category
echo -e "${BLUE}[4] Getting Electronics products${NC}"
curl -s "$API_URL/products?category=Electronics" | jq .
echo ""

# Test 5: Create a valid order
echo -e "${BLUE}[5] Creating a valid order${NC}"
ORDER_RESPONSE=$(curl -s -X POST "$API_URL/orders" \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": 1,
    "quantity": 2,
    "customer_name": "Alice Smith",
    "customer_email": "alice@example.com"
  }')
echo "$ORDER_RESPONSE" | jq .
ORDER_ID=$(echo "$ORDER_RESPONSE" | jq -r '.id')
echo ""

# Test 6: Get the created order
echo -e "${BLUE}[6] Getting order #${ORDER_ID}${NC}"
curl -s "$API_URL/orders/$ORDER_ID" | jq .
echo ""

# Test 7: Create an invalid order (product doesn't exist)
echo -e "${BLUE}[7] Attempting to create order with invalid product (should fail)${NC}"
curl -s -X POST "$API_URL/orders" \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": 999,
    "quantity": 1,
    "customer_name": "Bob Jones",
    "customer_email": "bob@example.com"
  }' | jq .
echo ""

# Test 8: Get non-existent product (should fail)
echo -e "${BLUE}[8] Attempting to get non-existent product (should fail)${NC}"
curl -s "$API_URL/products/999" | jq .
echo ""

# Test 9: Create multiple orders to generate traffic
echo -e "${BLUE}[9] Creating multiple orders for demo purposes${NC}"
for i in {1..5}; do
  PRODUCT_ID=$((1 + RANDOM % 5))
  QUANTITY=$((1 + RANDOM % 3))
  echo "  Creating order for product #${PRODUCT_ID} (quantity: ${QUANTITY})"
  curl -s -X POST "$API_URL/orders" \
    -H "Content-Type: application/json" \
    -d "{
      \"product_id\": ${PRODUCT_ID},
      \"quantity\": ${QUANTITY},
      \"customer_name\": \"Customer ${i}\",
      \"customer_email\": \"customer${i}@example.com\"
    }" > /dev/null
done
echo ""

echo -e "${GREEN}=========================================="
echo "Test completed successfully!"
echo "==========================================${NC}"
echo ""
echo "Now check Grafana to see the logs and traces:"
echo "  - Grafana: http://localhost:3000"
echo "  - Go to Explore -> Loki to see logs"
echo "  - Go to Explore -> Tempo to see traces"
echo ""
