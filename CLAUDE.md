# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Medical AI Risk Factor Profiling API** - Production-grade health checkup risk assessment system for JLK portfolio demo.

- **Purpose**: Portfolio demonstration of production ML inference backend
- **Data**: 1M Korean National Health Insurance health checkup records
- **Tech Stack**: Flask, MySQL (Railway), Redis, Chart.js, Tailwind CSS
- **Deployment**: Railway (auto-deploy from GitHub main branch)
- **Live Demo**: https://medical-ai-serving-api-production.up.railway.app/demo

## Architecture

### Data Pipeline (ETL)
```
CSV (1M records)
  → raw_health_check (1M records, all data)
  → ETL validation & risk calculation
  → clean_risk_result (340K records, valid only)
```

**Key Decision**: Invalid records (659K) are NOT stored in clean_risk_result table. Only biologically valid data (340K) is kept.

### Database Schema

**raw_health_check** (1M records)
- Original health checkup data from CSV
- Fields: age_group_code (5-18), gender_code (1-2), height, weight, BP, glucose, cholesterol, etc.
- Age groups: 5=25-29세, 6=30-34세, ..., 18=90세 초과

**clean_risk_result** (340K valid records only)
- Processed risk assessment results
- 7 risk factor flags: hypertension, diabetes, high_tc, high_tg, low_hdl, obesity, smoking
- Risk groups: ZERO_TO_ONE_RISK_FACTOR (64%), MULTIPLE_RISK_FACTORS (27%), CHD_RISK_EQUIVALENT (9%)
- NO invalid_flag filter needed - all records are valid

### API Endpoints

**GET /stats/risk** - Risk distribution (cached 60s)
**GET /stats/age** - Age distribution (cached 60s)
**GET /records** - Paginated records with filters (age_group, gender, risk_group)
**POST /simulate** - Real-time risk calculation
**GET /demo** - Interactive demo page

### Caching Strategy
- Redis Cache-Aside pattern
- 60s TTL for stats endpoints
- 99.8% performance improvement (4ms avg response)

## Key Files

### Backend
- `app/__init__.py` - Flask app factory, blueprint registration
- `app/blueprints/stats.py` - Statistics APIs (NO invalid_flag filters)
- `app/blueprints/records.py` - Records query with server-side filtering
- `app/blueprints/simulate.py` - Real-time risk calculation (age_group: 5-18)
- `app/cache.py` - Redis caching decorator
- `app/models/health_check.py` - SQLAlchemy models

### ETL Scripts
- `scripts/etl/load_raw.py` - Load CSV → raw_health_check
- `scripts/etl/process_clean.py` - Calculate risks, save ONLY valid records

### Frontend
- `app/templates/demo.html` - Single-page interactive demo
  - Risk distribution pie chart (Chart.js)
  - Age distribution bar chart
  - Records table with filters
  - Real-time simulation form
  - JLK brand colors: #5B21B6, #3B82F6, #06B6D4

## Recent Major Changes

### ETL Pipeline Modification (Latest)
**Issue**: Why store invalid records in clean table?
**Solution**: Modified ETL to skip saving invalid records entirely
- Updated `process_clean.py`: Only append valid records to batch
- Removed all `invalid_flag == False` filters from stats.py and records.py
- Truncated clean_risk_result and re-ran ETL on Railway
- Result: Clean table has 340K valid records, no invalid data

### Demo Page Improvements
- Fixed age group display: Consistent Korean format (25-29세, 30-34세, ..., 90세 초과)
- Added complete age group options (5-18) in all dropdowns
- Fixed filtering: Replaced broken client-side filtering with proper server-side
- Added gender filter support to records API
- Improved chart tooltips and legend visibility
- Default simulation shows 4/7 risk factors with detailed explanations

### Railway Deployment
- Port configuration: Container listens on 5001 (local) or 8080 (Railway)
- Auto-deployment from GitHub main branch
- Environment variables: API_KEY, DATABASE_URL, REDIS_URL, PORT
- Used public TCP proxy (yamanote.proxy.rlwy.net:25922) for local ETL runs
- Note: Railway's PORT environment variable overrides the default 5001

## Development Commands

### Local Development
```bash
# Start Flask dev server
python run.py  # Runs on port 5001 by default

# Or use Flask CLI directly
python -m flask run --host=0.0.0.0 --port=5001

# Or use gunicorn (production-like)
gunicorn -w 4 -b 0.0.0.0:5001 app:create_app()
```

### ETL Pipeline
```bash
# 1. Load CSV data to raw table (local MySQL)
python scripts/etl/load_raw.py

# 2. Process and calculate risks (local MySQL)
python scripts/etl/process_clean.py

# 3. Process to Railway MySQL (use public proxy)
DATABASE_URL="mysql+pymysql://root:PASSWORD@yamanote.proxy.rlwy.net:25922/railway" \
python scripts/etl/process_clean.py
```

### Railway Deployment
```bash
# Deploy to Railway
railway up

# Check logs
railway logs

# Connect to Railway MySQL
railway connect mysql
```

### Git Workflow
```bash
# User handles all git operations
# Just provide commit messages when requested
# Format: Title (imperative) + body + Co-Authored-By: Claude Sonnet 4.5
```

## Important Constraints

### Age Group Validation
- Valid range: 5-18 (25세-90세 초과)
- Update both demo.html dropdowns AND simulate.py validation when changing

### Data Integrity Rules
- clean_risk_result contains ONLY valid records
- NO invalid_flag filtering needed in queries
- raw_health_check is source of truth for total count

### API Design Principles
- Server-side filtering (pass filters as query params)
- NO client-side filtering/pagination hacks
- Proper error handling with descriptive messages
- Caching for read-heavy endpoints

### UI/UX Guidelines
- Use JLK brand colors consistently
- Text visibility: Use gray-200 or lighter on dark backgrounds
- Korean age format: "25-29세", "90세 초과"
- Risk factor details: Show thresholds and values (e.g., "Diabetes: glucose 130 >= 126")
- NO auto-loading stats - user must click buttons

## Common Issues & Solutions

### "Failed to load records" with filters
**Cause**: Client-side filtering or missing API filter support
**Fix**: Ensure filters are passed as URL query params, API supports all filters

### Age group display inconsistency
**Cause**: Incomplete age mapping in getAgeDisplay()
**Fix**: Use formula: `${ageGroup * 5}-${ageGroup * 5 + 4}세` for 5-17, special case for 18

### Invalid records in results
**Cause**: Querying with invalid_flag filters or wrong table
**Fix**: Query clean_risk_result directly (all valid), no filters needed

### Tooltip/legend text not visible
**Cause**: Dark text color (gray-500) on dark background
**Fix**: Use gray-200 or lighter (#F3F4F6) with appropriate font weight

## Testing Checklist

When making changes, verify:
- [ ] All age groups (5-18) work in filters and simulation
- [ ] Records filtering returns correct count for each filter combination
- [ ] Stats endpoints show correct totals (1M raw, 340K valid, 659K invalid)
- [ ] Chart tooltips are readable and well-positioned
- [ ] Risk simulation shows detailed explanations with thresholds
- [ ] Commit and push trigger Railway auto-deployment
- [ ] Demo page works on Railway deployment URL

## Railway Configuration

**Networking**: Port configuration
- Local: 5001 (default from run.py)
- Railway: PORT environment variable (overrides default, typically 8080)

**Environment Variables**:
- `API_KEY`: 0WCeJCbW18-rlmiuKsyAboiPfFIMZUzOTqYgFQdUrRc
- `DATABASE_URL`: mysql+pymysql://root:PASSWORD@mysql.railway.internal:3306/railway
- `REDIS_URL`: redis://default:PASSWORD@redis.railway.internal:6379
- `FLASK_ENV`: production
- `FLASK_DEBUG`: False

**Deployment**: Auto-deploy on push to main branch (no railway.toml needed)

## Memory Notes

### Database
- Total raw records: 1,000,000
- Valid records in clean table: 340,686 (34.1%)
- Invalid records (not stored): 659,314 (65.9%)

### JLK Brand Colors
- Primary Purple: #5B21B6
- Blue: #3B82F6
- Cyan: #06B6D4
- Navy: #0F172A
- Coral: #F97316

### Risk Distribution (실제 데이터 기준)
- Low Risk (0-1 factors): 218,365 (64.1%)
- Multiple Risk (2+ factors): 91,280 (26.8%)
- High Risk (diabetes/CHD): 31,041 (9.1%)
- Total valid records: 340,686
