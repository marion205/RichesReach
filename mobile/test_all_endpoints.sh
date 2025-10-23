#!/bin/bash

# Comprehensive API Endpoint Testing Script
# Tests all mutations, GraphQL queries, and REST endpoints

API_BASE="http://127.0.0.1:8000"
AUTH_TOKEN=""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Test authentication and get token
test_auth() {
    log "Testing authentication..."
    
    response=$(curl -s -X POST "$API_BASE/api/auth/login/" \
        -H "Content-Type: application/json" \
        -d '{"email": "demo@example.com", "password": "demo123"}')
    
    if echo "$response" | jq -e '.success' > /dev/null 2>&1; then
        AUTH_TOKEN=$(echo "$response" | jq -r '.token')
        success "Authentication successful"
        log "Token: ${AUTH_TOKEN:0:20}..."
        return 0
    else
        error "Authentication failed"
        echo "$response" | jq .
        return 1
    fi
}

# Test REST endpoint
test_rest_endpoint() {
    local name="$1"
    local method="$2"
    local url="$3"
    local data="$4"
    local requires_auth="$5"
    
    local headers="Content-Type: application/json"
    if [ "$requires_auth" = "true" ] && [ -n "$AUTH_TOKEN" ]; then
        headers="$headers"$'\n'"Authorization: Bearer $AUTH_TOKEN"
    fi
    
    local curl_cmd="curl -s -X $method \"$url\" -H \"Content-Type: application/json\""
    
    if [ "$requires_auth" = "true" ] && [ -n "$AUTH_TOKEN" ]; then
        curl_cmd="$curl_cmd -H \"Authorization: Bearer $AUTH_TOKEN\""
    fi
    
    if [ -n "$data" ]; then
        curl_cmd="$curl_cmd -d '$data'"
    fi
    
    local response=$(eval $curl_cmd)
    local status_code=$(eval $curl_cmd -w "%{http_code}" -o /dev/null)
    
    case $status_code in
        200|201|202)
            success "$name: $status_code"
            ;;
        404)
            warning "$name: $status_code (Not implemented)"
            ;;
        401)
            warning "$name: $status_code (Unauthorized)"
            ;;
        400)
            error "$name: $status_code (Bad Request)"
            echo "$response" | jq . 2>/dev/null || echo "$response"
            ;;
        500)
            error "$name: $status_code (Server Error)"
            echo "$response" | jq . 2>/dev/null || echo "$response"
            ;;
        *)
            error "$name: $status_code"
            echo "$response" | jq . 2>/dev/null || echo "$response"
            ;;
    esac
}

# Test GraphQL endpoint
test_graphql() {
    local name="$1"
    local query="$2"
    local variables="$3"
    
    local data="{\"query\": \"$query\""
    if [ -n "$variables" ]; then
        data="$data, \"variables\": $variables"
    fi
    data="$data}"
    
    local curl_cmd="curl -s -X POST \"$API_BASE/graphql/\" -H \"Content-Type: application/json\""
    
    if [ -n "$AUTH_TOKEN" ]; then
        curl_cmd="$curl_cmd -H \"Authorization: Bearer $AUTH_TOKEN\""
    fi
    
    curl_cmd="$curl_cmd -d '$data'"
    
    local response=$(eval $curl_cmd)
    local status_code=$(eval $curl_cmd -w "%{http_code}" -o /dev/null)
    
    case $status_code in
        200)
            if echo "$response" | jq -e '.errors' > /dev/null 2>&1; then
                warning "$name: GraphQL errors found"
                echo "$response" | jq '.errors'
            else
                success "$name: $status_code"
            fi
            ;;
        400)
            error "$name: $status_code (Bad Request)"
            echo "$response" | jq . 2>/dev/null || echo "$response"
            ;;
        *)
            error "$name: $status_code"
            echo "$response" | jq . 2>/dev/null || echo "$response"
            ;;
    esac
}

# Main testing function
run_tests() {
    echo "🧪 RichesReach Version 2 - Comprehensive API Testing"
    echo "=================================================="
    
    # Test authentication
    if ! test_auth; then
        error "Cannot proceed without authentication"
        exit 1
    fi
    
    echo ""
    log "Testing REST Endpoints..."
    echo "========================"
    
    # Authentication endpoints
    test_rest_endpoint "Logout" "POST" "$API_BASE/api/auth/logout/" "" "true"
    test_rest_endpoint "Refresh Token" "POST" "$API_BASE/api/auth/refresh/" "" "true"
    
    # User management
    test_rest_endpoint "Get User Profile" "GET" "$API_BASE/api/user/profile/" "" "true"
    test_rest_endpoint "Update User Profile" "PUT" "$API_BASE/api/user/profile/" '{"name": "Updated Name"}' "true"
    
    # Portfolio management
    test_rest_endpoint "Get Portfolios" "GET" "$API_BASE/api/portfolio/" "" "true"
    test_rest_endpoint "Create Portfolio" "POST" "$API_BASE/api/portfolio/" '{"name": "Test Portfolio", "description": "Test"}' "true"
    test_rest_endpoint "Get Portfolio" "GET" "$API_BASE/api/portfolio/1/" "" "true"
    test_rest_endpoint "Update Portfolio" "PUT" "$API_BASE/api/portfolio/1/" '{"name": "Updated Portfolio"}' "true"
    test_rest_endpoint "Delete Portfolio" "DELETE" "$API_BASE/api/portfolio/1/" "" "true"
    
    # Holdings management
    test_rest_endpoint "Get Holdings" "GET" "$API_BASE/api/portfolio/1/holdings/" "" "true"
    test_rest_endpoint "Add Holding" "POST" "$API_BASE/api/portfolio/1/holdings/" '{"symbol": "AAPL", "shares": 10, "purchasePrice": 150.00}' "true"
    test_rest_endpoint "Update Holding" "PUT" "$API_BASE/api/portfolio/1/holdings/1/" '{"shares": 15}' "true"
    test_rest_endpoint "Delete Holding" "DELETE" "$API_BASE/api/portfolio/1/holdings/1/" "" "true"
    
    # Market data
    test_rest_endpoint "Get Market Quotes" "GET" "$API_BASE/api/market/quotes/?symbols=AAPL,MSFT,GOOGL" "" "false"
    test_rest_endpoint "Get Market News" "GET" "$API_BASE/api/market/news/" "" "false"
    test_rest_endpoint "Get Market Analysis" "GET" "$API_BASE/api/market/analysis/?symbol=AAPL" "" "false"
    
    # Version 2 features
    test_rest_endpoint "Oracle Insights" "GET" "$API_BASE/api/oracle/insights/?portfolioId=1" "" "true"
    test_rest_endpoint "Voice AI Assistant" "POST" "$API_BASE/api/voice/process/" '{"text": "What is my portfolio performance?", "language": "en"}' "true"
    test_rest_endpoint "Wellness Score" "GET" "$API_BASE/api/portfolio/1/wellness/" "" "true"
    test_rest_endpoint "AR Portfolio Data" "GET" "$API_BASE/api/portfolio/1/ar/" "" "true"
    test_rest_endpoint "Blockchain Status" "GET" "$API_BASE/api/blockchain/status/" "" "true"
    test_rest_endpoint "Social Trading" "GET" "$API_BASE/api/social/trading/" "" "true"
    test_rest_endpoint "Wealth Circles" "GET" "$API_BASE/api/wealth-circles/" "" "true"
    test_rest_endpoint "Theme Settings" "GET" "$API_BASE/api/user/theme/" "" "true"
    test_rest_endpoint "Update Theme Settings" "PUT" "$API_BASE/api/user/theme/" '{"theme": "dark", "primaryColor": "#8B5CF6"}' "true"
    test_rest_endpoint "Security Settings" "GET" "$API_BASE/api/user/security/" "" "true"
    test_rest_endpoint "Update Security Settings" "PUT" "$API_BASE/api/user/security/" '{"biometricAuth": true, "twoFactorAuth": false}' "true"
    test_rest_endpoint "Viral Growth Data" "GET" "$API_BASE/api/viral-growth/" "" "true"
    test_rest_endpoint "Scalability Metrics" "GET" "$API_BASE/api/system/scalability/" "" "true"
    test_rest_endpoint "Marketing Metrics" "GET" "$API_BASE/api/marketing/metrics/" "" "true"
    
    echo ""
    log "Testing GraphQL Operations..."
    echo "============================"
    
    # GraphQL queries
    test_graphql "Get User Profile" "query { me { id email username name hasPremiumAccess } }"
    test_graphql "Get Portfolios" "query { portfolios { id name totalValue totalReturn } }"
    test_graphql "Get Market Data" "query { marketData(symbols: [\"AAPL\", \"MSFT\"]) { symbol price change } }"
    test_graphql "Get News" "query { news(limit: 5) { id title summary publishedAt } }"
    
    # GraphQL mutations
    test_graphql "Create Portfolio" "mutation { createPortfolio(input: {name: \"Test Portfolio\"}) { portfolio { id name } success } }"
    test_graphql "Add Holding" "mutation { addHolding(portfolioId: \"1\", input: {symbol: \"AAPL\", shares: 10}) { holding { id symbol } success } }"
    
    # Version 2 GraphQL
    test_graphql "Oracle Insights" "query { oracleInsights(portfolioId: \"1\") { insights { type title confidence } } }"
    test_graphql "Wellness Score" "query { wellnessScore(portfolioId: \"1\") { overallScore metrics { riskManagement diversification } } }"
    test_graphql "Blockchain Status" "query { blockchainStatus { networks { name status balance } } }"
    test_graphql "Social Trading" "query { socialTrading { signals { id trader symbol action } } }"
    test_graphql "Wealth Circles" "query { wealthCircles { id name category members } }"
    
    echo ""
    success "Comprehensive API testing completed!"
    
    echo ""
    log "Missing Endpoints Summary:"
    echo "========================"
    warning "The following endpoints need to be implemented:"
    echo "1. User Profile API"
    echo "2. Portfolio Management API"
    echo "3. Holdings Management API"
    echo "4. Market Data API"
    echo "5. News API"
    echo "6. Oracle Insights API"
    echo "7. Voice AI Assistant API"
    echo "8. Wellness Score API"
    echo "9. AR Portfolio API"
    echo "10. Blockchain Integration API"
    echo "11. Social Trading API"
    echo "12. Wealth Circles API"
    echo "13. Theme Settings API"
    echo "14. Security Settings API"
    echo "15. Viral Growth API"
    echo "16. Scalability Metrics API"
    echo "17. Marketing Metrics API"
    echo "18. GraphQL Schema and Resolvers"
}

# Run the tests
run_tests
