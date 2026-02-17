#!/bin/bash

# API 테스트 스크립트

BASE_URL="http://localhost:5001"
API_KEY="medical-ai-secret-key-2026"

echo "========================================="
echo "Medical AI API Test Script"
echo "========================================="
echo ""

# 1. Health check
echo "1. Health Check"
curl -s "$BASE_URL/health" | python3 -m json.tool
echo ""

# 2. GET /records (first page)
echo "2. GET /records (페이징)"
curl -s -H "X-API-KEY: $API_KEY" \
  "$BASE_URL/records?page=1&limit=5" | python3 -m json.tool
echo ""

# 3. GET /records/{id}
echo "3. GET /records/1 (단건 조회)"
curl -s -H "X-API-KEY: $API_KEY" \
  "$BASE_URL/records/1" | python3 -m json.tool
echo ""

# 4. GET /stats/risk
echo "4. GET /stats/risk (위험군 통계)"
curl -s -H "X-API-KEY: $API_KEY" \
  "$BASE_URL/stats/risk" | python3 -m json.tool
echo ""

# 5. GET /stats/age
echo "5. GET /stats/age (연령대 통계)"
curl -s -H "X-API-KEY: $API_KEY" \
  "$BASE_URL/stats/age" | python3 -m json.tool
echo ""

# 6. POST /simulate
echo "6. POST /simulate (위험도 계산)"
curl -s -X POST \
  -H "X-API-KEY: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "age_group": 12,
    "gender": 1,
    "height": 170,
    "weight": 85,
    "systolic_bp": 152,
    "diastolic_bp": 96,
    "fasting_glucose": 131,
    "total_cholesterol": 255,
    "triglycerides": 210,
    "hdl_cholesterol": 38,
    "smoking_status": "current"
  }' \
  "$BASE_URL/simulate" | python3 -m json.tool
echo ""

echo "========================================="
echo "Tests Complete!"
echo "========================================="
