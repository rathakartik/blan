#!/bin/bash

# =============================================================================
# AI VOICE ASSISTANT PLATFORM - COMPREHENSIVE START SCRIPT
# =============================================================================
# This script provides comprehensive management for the AI Voice Assistant
# platform including MongoDB database, FastAPI backend, and React frontend.
# 
# Platform: Kubernetes Container Environment with Supervisor
# Database: MongoDB (managed by supervisor, not Docker)
# Backend: FastAPI with GROQ AI Integration
# Frontend: React with Tailwind CSS
# =============================================================================

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Configuration
APP_ROOT="/app"
BACKEND_DIR="$APP_ROOT/backend"
FRONTEND_DIR="$APP_ROOT/frontend"
LOG_DIR="/var/log/supervisor"
PID_FILE="/tmp/ai_assistant_monitoring.pid"

# Service configuration
SERVICES=("mongodb" "backend" "frontend")
REQUIRED_PORTS=(27017 8001 3000)

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

print_banner() {
    echo -e "${CYAN}╔══════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║                AI VOICE ASSISTANT PLATFORM MANAGER                  ║${NC}"
    echo -e "${CYAN}║                     Comprehensive Service Control                   ║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

print_section() {
    echo -e "\n${BLUE}┌─────────────────────────────────────────────────────────────────────┐${NC}"
    echo -e "${BLUE}│ $1${NC}"
    echo -e "${BLUE}└─────────────────────────────────────────────────────────────────────┘${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

print_step() {
    echo -e "${PURPLE}🔧 $1${NC}"
}

# Check if running as root (optional for some operations)
check_permissions() {
    if [[ $EUID -eq 0 ]]; then
        print_info "Running as root - all operations available"
    else
        print_warning "Running as non-root - some operations may require sudo"
    fi
}

# Check if supervisor is available
check_supervisor() {
    if ! command -v supervisorctl &> /dev/null; then
        print_error "supervisorctl not found - this script requires supervisor"
        exit 1
    fi
    print_success "Supervisor is available"
}

# =============================================================================
# SERVICE MANAGEMENT FUNCTIONS
# =============================================================================

get_service_status() {
    local service=$1
    local status=$(supervisorctl status $service 2>/dev/null | awk '{print $2}')
    echo $status
}

get_service_pid() {
    local service=$1
    local pid=$(supervisorctl status $service 2>/dev/null | grep -o 'pid [0-9]*' | awk '{print $2}')
    echo $pid
}

get_service_uptime() {
    local service=$1
    local uptime=$(supervisorctl status $service 2>/dev/null | grep -o 'uptime [^,]*' | sed 's/uptime //')
    echo $uptime
}

show_service_status() {
    print_section "SERVICE STATUS OVERVIEW"
    
    echo -e "${WHITE}Service${NC}\t\t${WHITE}Status${NC}\t\t${WHITE}PID${NC}\t\t${WHITE}Uptime${NC}"
    echo -e "─────────────────────────────────────────────────────────────"
    
    for service in "${SERVICES[@]}"; do
        local status=$(get_service_status $service)
        local pid=$(get_service_pid $service)
        local uptime=$(get_service_uptime $service)
        
        case $status in
            "RUNNING")
                echo -e "${service}\t\t${GREEN}${status}${NC}\t\t${pid}\t\t${uptime}"
                ;;
            "STOPPED"|"FATAL"|"EXITED")
                echo -e "${service}\t\t${RED}${status}${NC}\t\t${pid}\t\t${uptime}"
                ;;
            *)
                echo -e "${service}\t\t${YELLOW}${status}${NC}\t\t${pid}\t\t${uptime}"
                ;;
        esac
    done
    
    echo ""
}

start_services() {
    print_section "STARTING ALL SERVICES"
    
    # Start MongoDB first (if not running)
    if [[ $(get_service_status mongodb) != "RUNNING" ]]; then
        print_step "Starting MongoDB..."
        supervisorctl start mongodb
        sleep 3
        
        if [[ $(get_service_status mongodb) == "RUNNING" ]]; then
            print_success "MongoDB started successfully"
        else
            print_error "Failed to start MongoDB"
            return 1
        fi
    else
        print_success "MongoDB is already running"
    fi
    
    # Start Backend
    if [[ $(get_service_status backend) != "RUNNING" ]]; then
        print_step "Starting Backend API..."
        supervisorctl start backend
        sleep 3
        
        if [[ $(get_service_status backend) == "RUNNING" ]]; then
            print_success "Backend API started successfully"
        else
            print_error "Failed to start Backend API"
            return 1
        fi
    else
        print_success "Backend API is already running"
    fi
    
    # Start Frontend
    if [[ $(get_service_status frontend) != "RUNNING" ]]; then
        print_step "Starting Frontend..."
        supervisorctl start frontend
        sleep 3
        
        if [[ $(get_service_status frontend) == "RUNNING" ]]; then
            print_success "Frontend started successfully"
        else
            print_error "Failed to start Frontend"
            return 1
        fi
    else
        print_success "Frontend is already running"
    fi
    
    print_success "All services are now running!"
}

stop_services() {
    print_section "STOPPING ALL SERVICES"
    
    for service in "${SERVICES[@]}"; do
        if [[ $(get_service_status $service) == "RUNNING" ]]; then
            print_step "Stopping $service..."
            supervisorctl stop $service
            print_success "$service stopped"
        else
            print_info "$service is already stopped"
        fi
    done
}

restart_services() {
    print_section "RESTARTING ALL SERVICES"
    
    print_step "Restarting all services..."
    supervisorctl restart mongodb backend frontend
    sleep 5
    
    show_service_status
}

# =============================================================================
# HEALTH CHECK FUNCTIONS
# =============================================================================

check_port() {
    local port=$1
    local service_name=$2
    
    if netstat -tlnp 2>/dev/null | grep -q ":$port "; then
        local pid=$(netstat -tlnp 2>/dev/null | grep ":$port " | awk '{print $7}' | cut -d'/' -f1)
        print_success "$service_name is listening on port $port (PID: $pid)"
        return 0
    else
        print_error "$service_name is NOT listening on port $port"
        return 1
    fi
}

check_mongodb_connection() {
    print_step "Testing MongoDB connection..."
    
    # Check if MongoDB is running on port 27017
    if check_port 27017 "MongoDB"; then
        # Test actual connection
        if mongo --eval "db.stats()" ai_voice_assistant &>/dev/null; then
            print_success "MongoDB connection test passed"
            
            # Show database stats
            local db_stats=$(mongo --quiet --eval "
                var stats = db.stats();
                print('Collections: ' + stats.collections + ', Objects: ' + stats.objects + ', Data Size: ' + (stats.dataSize/1024/1024).toFixed(2) + 'MB');
            " ai_voice_assistant 2>/dev/null)
            print_info "Database stats: $db_stats"
            return 0
        else
            print_error "MongoDB connection failed"
            return 1
        fi
    else
        return 1
    fi
}

check_backend_api() {
    print_step "Testing Backend API..."
    
    # Check if backend is running on port 8001
    if check_port 8001 "Backend API"; then
        # Test health endpoint
        local health_response=$(curl -s http://localhost:8001/api/health 2>/dev/null || echo "error")
        
        if [[ $health_response == *"healthy"* ]]; then
            print_success "Backend API health check passed"
            
            # Extract key information
            local mongodb_status=$(echo $health_response | grep -o '"mongodb":{"status":"[^"]*"' | cut -d'"' -f8)
            local groq_status=$(echo $health_response | grep -o '"groq":{"status":"[^"]*"' | cut -d'"' -f8)
            
            print_info "MongoDB integration: $mongodb_status"
            print_info "GROQ AI integration: $groq_status"
            return 0
        else
            print_error "Backend API health check failed"
            return 1
        fi
    else
        return 1
    fi
}

check_frontend() {
    print_step "Testing Frontend application..."
    
    # Check if frontend is running on port 3000
    if check_port 3000 "Frontend"; then
        # Test if frontend is responding
        if curl -s http://localhost:3000 &>/dev/null; then
            print_success "Frontend is responding correctly"
            return 0
        else
            print_error "Frontend is not responding"
            return 1
        fi
    else
        return 1
    fi
}

comprehensive_health_check() {
    print_section "COMPREHENSIVE HEALTH CHECK"
    
    local all_healthy=true
    
    # Service status check
    for service in "${SERVICES[@]}"; do
        local status=$(get_service_status $service)
        if [[ $status != "RUNNING" ]]; then
            print_error "$service is not running (Status: $status)"
            all_healthy=false
        else
            print_success "$service is running"
        fi
    done
    
    # Connectivity checks
    check_mongodb_connection || all_healthy=false
    check_backend_api || all_healthy=false
    check_frontend || all_healthy=false
    
    # Environment checks
    print_step "Checking environment configuration..."
    if [[ -f "$BACKEND_DIR/.env" ]]; then
        print_success "Backend environment file exists"
        
        # Check critical environment variables
        if grep -q "MONGO_URL" "$BACKEND_DIR/.env"; then
            print_success "MongoDB URL configured"
        else
            print_warning "MongoDB URL not configured"
        fi
        
        if grep -q "GROQ_API_KEY" "$BACKEND_DIR/.env"; then
            print_success "GROQ API key configured"
        else
            print_warning "GROQ API key not configured (will use demo mode)"
        fi
    else
        print_error "Backend environment file missing"
        all_healthy=false
    fi
    
    if [[ -f "$FRONTEND_DIR/.env" ]]; then
        print_success "Frontend environment file exists"
    else
        print_error "Frontend environment file missing"
        all_healthy=false
    fi
    
    # Final status
    if $all_healthy; then
        print_success "All health checks passed! Platform is fully operational."
        return 0
    else
        print_error "Some health checks failed. Please review the issues above."
        return 1
    fi
}

# =============================================================================
# DEBUG AND LOGGING FUNCTIONS
# =============================================================================

show_logs() {
    local service=${1:-"all"}
    
    if [[ $service == "all" ]]; then
        print_section "SHOWING ALL SERVICE LOGS (LAST 20 LINES EACH)"
        
        for svc in "${SERVICES[@]}"; do
            echo -e "\n${PURPLE}=== $svc LOGS ===${NC}"
            if [[ -f "$LOG_DIR/$svc.log" ]]; then
                tail -n 20 "$LOG_DIR/$svc.log"
            elif [[ -f "$LOG_DIR/${svc}.out.log" ]]; then
                tail -n 20 "$LOG_DIR/${svc}.out.log"
            else
                print_warning "No log file found for $svc"
            fi
        done
    else
        print_section "SHOWING $service LOGS"
        
        # Show both stdout and stderr logs if available
        for ext in ".log" ".out.log" ".err.log"; do
            local log_file="$LOG_DIR/$service$ext"
            if [[ -f "$log_file" ]]; then
                echo -e "\n${PURPLE}=== $service$ext ===${NC}"
                tail -n 50 "$log_file"
            fi
        done
    fi
}

follow_logs() {
    local service=${1:-"backend"}
    
    print_section "FOLLOWING $service LOGS (Press Ctrl+C to stop)"
    
    local log_file="$LOG_DIR/$service.log"
    if [[ ! -f "$log_file" ]]; then
        log_file="$LOG_DIR/${service}.out.log"
    fi
    
    if [[ -f "$log_file" ]]; then
        tail -f "$log_file"
    else
        print_error "Log file not found for $service"
    fi
}

debug_connectivity() {
    print_section "DEBUGGING CONNECTIVITY ISSUES"
    
    # Test internal connectivity
    print_step "Testing internal service connectivity..."
    
    # MongoDB connectivity
    print_info "Testing MongoDB connection from backend..."
    cd "$BACKEND_DIR"
    if python3 -c "
import os
from pymongo import MongoClient
try:
    client = MongoClient(os.getenv('MONGO_URL', 'mongodb://localhost:27017/ai_voice_assistant'))
    client.admin.command('ping')
    print('✅ Backend can connect to MongoDB')
except Exception as e:
    print(f'❌ Backend cannot connect to MongoDB: {e}')
" 2>/dev/null; then
        true
    else
        print_error "Python MongoDB test failed"
    fi
    
    # Backend API connectivity
    print_info "Testing backend API endpoints..."
    local endpoints=("/api/health" "/api/status" "/")
    for endpoint in "${endpoints[@]}"; do
        if curl -s -o /dev/null -w "%{http_code}" "http://localhost:8001$endpoint" | grep -q "200"; then
            print_success "Endpoint $endpoint is responding"
        else
            print_warning "Endpoint $endpoint is not responding properly"
        fi
    done
    
    # Frontend to Backend connectivity
    print_info "Testing frontend environment configuration..."
    if [[ -f "$FRONTEND_DIR/.env" ]]; then
        local backend_url=$(grep "REACT_APP_BACKEND_URL" "$FRONTEND_DIR/.env" | cut -d'=' -f2)
        print_info "Frontend configured to use backend: $backend_url"
        
        if curl -s -o /dev/null "$backend_url/api/health"; then
            print_success "Frontend can reach backend URL"
        else
            print_warning "Frontend cannot reach configured backend URL"
        fi
    fi
    
    # Network configuration
    print_step "Checking network configuration..."
    echo -e "\n${WHITE}Active network connections:${NC}"
    netstat -tlnp | grep -E ':(3000|8001|27017) '
    
    echo -e "\n${WHITE}Process information:${NC}"
    ps aux | grep -E '(mongod|python|node)' | grep -v grep
}

# =============================================================================
# DEVELOPMENT TOOLS
# =============================================================================

install_dependencies() {
    print_section "INSTALLING/UPDATING DEPENDENCIES"
    
    # Backend dependencies
    print_step "Installing Python dependencies..."
    cd "$BACKEND_DIR"
    if [[ -f "requirements.txt" ]]; then
        pip install -r requirements.txt
        print_success "Python dependencies installed"
    else
        print_error "requirements.txt not found in backend directory"
    fi
    
    # Frontend dependencies  
    print_step "Installing Node.js dependencies..."
    cd "$FRONTEND_DIR"
    if [[ -f "package.json" ]]; then
        yarn install
        print_success "Node.js dependencies installed"
    else
        print_error "package.json not found in frontend directory"
    fi
    
    cd "$APP_ROOT"
}

database_operations() {
    print_section "DATABASE MANAGEMENT OPERATIONS"
    
    echo "Available operations:"
    echo "1. Show database statistics"
    echo "2. List collections"
    echo "3. Show users count"
    echo "4. Show sites count"
    echo "5. Show recent conversations"
    echo "6. Database backup"
    echo "7. Create database indexes"
    
    read -p "Select operation (1-7): " choice
    
    case $choice in
        1)
            print_step "Database Statistics:"
            mongo --quiet ai_voice_assistant --eval "db.stats()" 2>/dev/null
            ;;
        2)
            print_step "Collections:"
            mongo --quiet ai_voice_assistant --eval "db.getCollectionNames()" 2>/dev/null
            ;;
        3)
            print_step "Users count:"
            mongo --quiet ai_voice_assistant --eval "db.users.count()" 2>/dev/null
            ;;
        4)
            print_step "Sites count:"
            mongo --quiet ai_voice_assistant --eval "db.sites.count()" 2>/dev/null
            ;;
        5)
            print_step "Recent conversations (last 5):"
            mongo --quiet ai_voice_assistant --eval "db.conversations.find().sort({timestamp: -1}).limit(5).pretty()" 2>/dev/null
            ;;
        6)
            print_step "Creating database backup..."
            local backup_dir="/tmp/ai_assistant_backup_$(date +%Y%m%d_%H%M%S)"
            mongodump --db ai_voice_assistant --out "$backup_dir" 2>/dev/null
            print_success "Database backed up to: $backup_dir"
            ;;
        7)
            print_step "Creating database indexes..."
            mongo ai_voice_assistant --eval "
                db.users.createIndex({email: 1}, {unique: true});
                db.sites.createIndex({user_id: 1});
                db.sites.createIndex({domain: 1});
                db.conversations.createIndex({site_id: 1, timestamp: -1});
                db.interactions.createIndex({site_id: 1, timestamp: -1});
                print('Indexes created successfully');
            " 2>/dev/null
            ;;
        *)
            print_error "Invalid choice"
            ;;
    esac
}

performance_monitoring() {
    print_section "PERFORMANCE MONITORING"
    
    # System resources
    print_step "System Resource Usage:"
    echo -e "\n${WHITE}Memory Usage:${NC}"
    free -h
    
    echo -e "\n${WHITE}CPU Usage:${NC}"
    top -bn1 | grep "Cpu(s)" | awk '{print $2 " " $4}' | sed 's/%us,//; s/%id,//'
    
    echo -e "\n${WHITE}Disk Usage:${NC}"
    df -h /
    
    # Service resource usage
    print_step "Service Resource Usage:"
    for service in "${SERVICES[@]}"; do
        local pid=$(get_service_pid $service)
        if [[ -n "$pid" ]]; then
            local cpu_mem=$(ps -p $pid -o pid,pcpu,pmem,command --no-headers 2>/dev/null)
            if [[ -n "$cpu_mem" ]]; then
                echo -e "${WHITE}$service (PID: $pid):${NC} $cpu_mem"
            fi
        fi
    done
    
    # Database statistics
    print_step "Database Performance:"
    mongo --quiet ai_voice_assistant --eval "
        var stats = db.serverStatus();
        print('Connections: ' + stats.connections.current + '/' + stats.connections.available);
        print('Operations/sec: ' + stats.opcounters.command);
        var dbStats = db.stats();
        print('Collections: ' + dbStats.collections + ', Objects: ' + dbStats.objects);
        print('Data Size: ' + (dbStats.dataSize/1024/1024).toFixed(2) + 'MB');
    " 2>/dev/null
}

# =============================================================================
# SECURITY AND CONFIGURATION
# =============================================================================

security_audit() {
    print_section "SECURITY CONFIGURATION AUDIT"
    
    # Environment file security
    print_step "Checking environment file security..."
    
    for env_file in "$BACKEND_DIR/.env" "$FRONTEND_DIR/.env"; do
        if [[ -f "$env_file" ]]; then
            local perms=$(stat -c "%a" "$env_file")
            if [[ "$perms" == "600" ]] || [[ "$perms" == "640" ]]; then
                print_success "$(basename $env_file) has secure permissions ($perms)"
            else
                print_warning "$(basename $env_file) has potentially insecure permissions ($perms)"
                print_info "Consider running: chmod 600 $env_file"
            fi
        fi
    done
    
    # API Key configuration
    print_step "Checking API key configuration..."
    if grep -q "SECRET_KEY=your-secret-key-here-change-in-production" "$BACKEND_DIR/.env" 2>/dev/null; then
        print_warning "Default SECRET_KEY detected - should be changed in production"
    else
        print_success "SECRET_KEY appears to be configured"
    fi
    
    # MongoDB security
    print_step "Checking MongoDB configuration..."
    if mongo --quiet --eval "db.adminCommand('connectionStatus')" 2>/dev/null | grep -q "authenticated.*true"; then
        print_success "MongoDB authentication is enabled"
    else
        print_warning "MongoDB may not have authentication enabled"
    fi
    
    # CORS configuration
    print_step "Checking CORS configuration..."
    if grep -q 'allow_origins=\["*"\]' "$BACKEND_DIR/server.py" 2>/dev/null; then
        print_warning "CORS is configured to allow all origins - restrict in production"
    else
        print_success "CORS appears to be properly configured"
    fi
    
    # SSL/TLS
    print_step "Checking SSL/TLS configuration..."
    if [[ $(get_service_status frontend) == "RUNNING" ]]; then
        if curl -s -I http://localhost:3000 | grep -q "HTTP/1.1 200"; then
            print_info "Frontend is running on HTTP - consider HTTPS for production"
        fi
    fi
}

environment_setup() {
    print_section "ENVIRONMENT SETUP AND VALIDATION"
    
    # Check required directories
    print_step "Checking directory structure..."
    local required_dirs=("$BACKEND_DIR" "$FRONTEND_DIR" "$LOG_DIR")
    for dir in "${required_dirs[@]}"; do
        if [[ -d "$dir" ]]; then
            print_success "Directory exists: $dir"
        else
            print_error "Missing directory: $dir"
        fi
    done
    
    # Check required files
    print_step "Checking required files..."
    local required_files=(
        "$BACKEND_DIR/server.py"
        "$BACKEND_DIR/requirements.txt"
        "$BACKEND_DIR/.env"
        "$FRONTEND_DIR/package.json"
        "$FRONTEND_DIR/.env"
    )
    
    for file in "${required_files[@]}"; do
        if [[ -f "$file" ]]; then
            print_success "File exists: $(basename $file)"
        else
            print_error "Missing file: $file"
        fi
    done
    
    # Environment variable validation
    print_step "Validating environment variables..."
    cd "$BACKEND_DIR"
    
    # Check MongoDB URL
    if python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()
mongo_url = os.getenv('MONGO_URL')
if mongo_url and 'mongodb://' in mongo_url:
    print('✅ MONGO_URL is properly formatted')
else:
    print('❌ MONGO_URL is missing or malformed')
" 2>/dev/null; then
        true
    fi
    
    # Check GROQ API Key
    if grep -q "GROQ_API_KEY=gsk_" "$BACKEND_DIR/.env"; then
        print_success "GROQ API key appears to be configured"
    else
        print_warning "GROQ API key may not be configured (will use demo mode)"
    fi
    
    cd "$APP_ROOT"
}

# =============================================================================
# MONITORING AND ALERTS
# =============================================================================

start_monitoring() {
    print_section "STARTING CONTINUOUS MONITORING"
    
    if [[ -f "$PID_FILE" ]] && ps -p $(cat "$PID_FILE") > /dev/null 2>&1; then
        print_warning "Monitoring is already running (PID: $(cat "$PID_FILE"))"
        return 1
    fi
    
    print_step "Starting background monitoring process..."
    
    (
        while true; do
            # Check service health every 30 seconds
            for service in "${SERVICES[@]}"; do
                if [[ $(get_service_status $service) != "RUNNING" ]]; then
                    echo "$(date): WARNING - $service is not running" >> /tmp/ai_assistant_alerts.log
                    # Could send notification here
                fi
            done
            
            # Check disk space
            disk_usage=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
            if [[ $disk_usage -gt 90 ]]; then
                echo "$(date): WARNING - Disk usage is ${disk_usage}%" >> /tmp/ai_assistant_alerts.log
            fi
            
            # Check memory usage
            mem_usage=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
            if [[ $mem_usage -gt 90 ]]; then
                echo "$(date): WARNING - Memory usage is ${mem_usage}%" >> /tmp/ai_assistant_alerts.log
            fi
            
            sleep 30
        done
    ) &
    
    echo $! > "$PID_FILE"
    print_success "Monitoring started (PID: $!)"
    print_info "Alerts will be logged to: /tmp/ai_assistant_alerts.log"
}

stop_monitoring() {
    if [[ -f "$PID_FILE" ]] && ps -p $(cat "$PID_FILE") > /dev/null 2>&1; then
        kill $(cat "$PID_FILE")
        rm -f "$PID_FILE"
        print_success "Monitoring stopped"
    else
        print_info "Monitoring is not running"
    fi
}

show_alerts() {
    if [[ -f "/tmp/ai_assistant_alerts.log" ]]; then
        print_section "RECENT ALERTS"
        tail -n 20 /tmp/ai_assistant_alerts.log
    else
        print_info "No alerts found"
    fi
}

# =============================================================================
# WIDGET AND INTEGRATION TESTING
# =============================================================================

test_widget_system() {
    print_section "TESTING WIDGET SYSTEM"
    
    # Test widget configuration endpoint
    print_step "Testing widget configuration endpoint..."
    local widget_response=$(curl -s -X POST http://localhost:8001/api/widget/config \
        -H "Content-Type: application/json" \
        -d '{"site_id": "demo"}' 2>/dev/null)
    
    if echo "$widget_response" | grep -q "greeting_message"; then
        print_success "Widget configuration endpoint is working"
    else
        print_error "Widget configuration endpoint failed"
    fi
    
    # Test chat endpoint
    print_step "Testing AI chat endpoint..."
    local chat_response=$(curl -s -X POST http://localhost:8001/api/chat \
        -H "Content-Type: application/json" \
        -d '{"message": "Hello", "session_id": "test", "site_id": "demo"}' 2>/dev/null)
    
    if echo "$chat_response" | grep -q "response"; then
        print_success "AI chat endpoint is working"
        local model=$(echo "$chat_response" | grep -o '"model":"[^"]*"' | cut -d'"' -f4)
        print_info "Using AI model: $model"
    else
        print_error "AI chat endpoint failed"
    fi
    
    # Test static files
    print_step "Testing widget static files..."
    local static_files=("widget.js" "widget.html" "embed.js")
    for file in "${static_files[@]}"; do
        if curl -s -o /dev/null -w "%{http_code}" "http://localhost:8001/static/$file" | grep -q "200"; then
            print_success "Static file $file is accessible"
        else
            print_warning "Static file $file is not accessible"
        fi
    done
    
    # Test analytics endpoint
    print_step "Testing analytics endpoint..."
    local analytics_response=$(curl -s -X POST http://localhost:8001/api/analytics/interaction \
        -H "Content-Type: application/json" \
        -d '{"site_id": "demo", "session_id": "test", "type": "test"}' 2>/dev/null)
    
    if echo "$analytics_response" | grep -q "logged"; then
        print_success "Analytics endpoint is working"
    else
        print_warning "Analytics endpoint may have issues"
    fi
}

# =============================================================================
# MAIN MENU AND COMMAND HANDLING
# =============================================================================

show_help() {
    print_banner
    echo -e "${WHITE}USAGE:${NC} $0 [command] [options]"
    echo ""
    echo -e "${WHITE}COMMANDS:${NC}"
    echo -e "  ${GREEN}start${NC}              Start all services (MongoDB, Backend, Frontend)"
    echo -e "  ${GREEN}stop${NC}               Stop all services"
    echo -e "  ${GREEN}restart${NC}            Restart all services"
    echo -e "  ${GREEN}status${NC}             Show service status overview"
    echo -e "  ${GREEN}health${NC}             Run comprehensive health check"
    echo -e "  ${GREEN}logs [service]${NC}     Show logs (all services or specific: mongodb/backend/frontend)"
    echo -e "  ${GREEN}follow [service]${NC}   Follow logs in real-time (default: backend)"
    echo -e "  ${GREEN}debug${NC}              Debug connectivity issues"
    echo -e "  ${GREEN}install${NC}            Install/update dependencies"
    echo -e "  ${GREEN}database${NC}           Database management operations"
    echo -e "  ${GREEN}monitor${NC}            Performance monitoring"
    echo -e "  ${GREEN}security${NC}           Security configuration audit"
    echo -e "  ${GREEN}setup${NC}              Environment setup and validation"
    echo -e "  ${GREEN}watch-start${NC}        Start continuous monitoring"
    echo -e "  ${GREEN}watch-stop${NC}         Stop continuous monitoring"
    echo -e "  ${GREEN}alerts${NC}             Show recent alerts"
    echo -e "  ${GREEN}test-widget${NC}        Test widget system functionality"
    echo -e "  ${GREEN}interactive${NC}        Interactive menu mode"
    echo ""
    echo -e "${WHITE}EXAMPLES:${NC}"
    echo -e "  $0 start                Start all services"
    echo -e "  $0 health               Run health check"
    echo -e "  $0 logs backend         Show backend logs"
    echo -e "  $0 follow frontend      Follow frontend logs"
    echo -e "  $0 debug                Debug connectivity issues"
    echo ""
}

interactive_menu() {
    while true; do
        print_banner
        echo -e "${WHITE}INTERACTIVE MENU${NC}"
        echo ""
        echo -e "1.  ${GREEN}Service Status${NC}           - Show current service status"
        echo -e "2.  ${GREEN}Start All Services${NC}       - Start MongoDB, Backend, Frontend"
        echo -e "3.  ${GREEN}Stop All Services${NC}        - Stop all services"
        echo -e "4.  ${GREEN}Restart All Services${NC}     - Restart all services"
        echo -e "5.  ${GREEN}Health Check${NC}             - Comprehensive health check"
        echo -e "6.  ${GREEN}Show Logs${NC}                - View service logs"
        echo -e "7.  ${GREEN}Debug Connectivity${NC}       - Debug connection issues"
        echo -e "8.  ${GREEN}Install Dependencies${NC}     - Update Python/Node dependencies"
        echo -e "9.  ${GREEN}Database Management${NC}      - Database operations"
        echo -e "10. ${GREEN}Performance Monitor${NC}      - System performance monitoring"
        echo -e "11. ${GREEN}Security Audit${NC}           - Security configuration check"
        echo -e "12. ${GREEN}Test Widget System${NC}       - Test widget functionality"
        echo -e "13. ${GREEN}Environment Setup${NC}        - Validate environment configuration"
        echo -e "14. ${GREEN}Start Monitoring${NC}         - Start continuous monitoring"
        echo -e "15. ${GREEN}Show Alerts${NC}              - View recent system alerts"
        echo -e "0.  ${RED}Exit${NC}"
        echo ""
        read -p "Select option (0-15): " choice
        
        case $choice in
            1) show_service_status ;;
            2) start_services ;;
            3) stop_services ;;
            4) restart_services ;;
            5) comprehensive_health_check ;;
            6) 
                echo "Select service (all/mongodb/backend/frontend): "
                read service
                show_logs "$service"
                ;;
            7) debug_connectivity ;;
            8) install_dependencies ;;
            9) database_operations ;;
            10) performance_monitoring ;;
            11) security_audit ;;
            12) test_widget_system ;;
            13) environment_setup ;;
            14) start_monitoring ;;
            15) show_alerts ;;
            0) print_success "Goodbye!"; exit 0 ;;
            *) print_error "Invalid option" ;;
        esac
        
        echo ""
        read -p "Press Enter to continue..."
    done
}

# =============================================================================
# MAIN SCRIPT EXECUTION
# =============================================================================

# Initial checks
check_permissions
check_supervisor

# Handle command line arguments
case "${1:-interactive}" in
    "start")
        print_banner
        start_services
        ;;
    "stop")
        print_banner
        stop_services
        ;;
    "restart")
        print_banner
        restart_services
        ;;
    "status")
        print_banner
        show_service_status
        ;;
    "health")
        print_banner
        comprehensive_health_check
        ;;
    "logs")
        print_banner
        show_logs "$2"
        ;;
    "follow")
        follow_logs "${2:-backend}"
        ;;
    "debug")
        print_banner
        debug_connectivity
        ;;
    "install")
        print_banner
        install_dependencies
        ;;
    "database")
        print_banner
        database_operations
        ;;
    "monitor")
        print_banner
        performance_monitoring
        ;;
    "security")
        print_banner
        security_audit
        ;;
    "setup")
        print_banner
        environment_setup
        ;;
    "watch-start")
        start_monitoring
        ;;
    "watch-stop")
        stop_monitoring
        ;;
    "alerts")
        show_alerts
        ;;
    "test-widget")
        print_banner
        test_widget_system
        ;;
    "interactive")
        interactive_menu
        ;;
    "help"|"--help"|"-h")
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac

print_success "Script execution completed!"