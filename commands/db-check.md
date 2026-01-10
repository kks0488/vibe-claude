# Database Check Skill

Database connection check skill. Tests Supabase/PostgreSQL connections.

## Usage

```
/db-check [options]
```

## Options

- `--tables` - List tables
- `--schema [table]` - Query specific table schema
- `--sample [table]` - Query sample data
- `--stats` - Table statistics
- `--keywords` - Keyword-related tables only

## Instructions

You are a Database Administrator. When this skill is invoked:

### 1. Connection Test

```bash
cd /home/kkaemo/projects/naver-trend-intelligence/data_integration
export $(grep -v '^#' api/.env | xargs)

python3 -c "
import psycopg2
from urllib.parse import urlparse

url = '$DATABASE_URL'
result = urlparse(url)

try:
    conn = psycopg2.connect(
        database=result.path[1:],
        user=result.username,
        password=result.password,
        host=result.hostname,
        port=result.port
    )
    print('Connection successful')
    print(f'  Host: {result.hostname}:{result.port}')
    print(f'  Database: {result.path[1:]}')
    conn.close()
except Exception as e:
    print(f'Connection failed: {e}')
"
```

### 2. Table List Query (`--tables`)

```python
cur.execute('''
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'public'
    ORDER BY table_name
''')
tables = cur.fetchall()
print(f'Table count: {len(tables)}')
for t in tables:
    print(f'  - {t[0]}')
```

### 3. Table Schema Query (`--schema`)

```python
cur.execute('''
    SELECT column_name, data_type, is_nullable
    FROM information_schema.columns
    WHERE table_name = %s
    ORDER BY ordinal_position
''', (table_name,))
```

### 4. Keyword Table Analysis (`--keywords`)

```python
# daily_keywords table
cur.execute('''
    SELECT
        COUNT(*) as total,
        MIN(scrape_date) as first_date,
        MAX(scrape_date) as last_date,
        COUNT(DISTINCT keyword) as unique_keywords
    FROM daily_keywords
''')

# Recent top keywords
cur.execute('''
    SELECT keyword, keyword_rank
    FROM daily_keywords
    WHERE scrape_date = (SELECT MAX(scrape_date) FROM daily_keywords)
    ORDER BY keyword_rank
    LIMIT 10
''')
```

### 5. Table Statistics (`--stats`)

```python
cur.execute('''
    SELECT
        relname as table_name,
        n_live_tup as row_count
    FROM pg_stat_user_tables
    ORDER BY n_live_tup DESC
    LIMIT 20
''')
```

## Quick Commands

```bash
# Connection check only
/db-check

# Keyword tables check
/db-check --keywords

# Specific table schema
/db-check --schema daily_keywords

# Full statistics
/db-check --stats
```

## Output Format

```
## Database Check Report

### Connection Status
- Host: [hostname:port]
- Database: [name]
- Status: Connected / Connection failed

### Table Status (--tables)
- Total tables: N
- Main tables:
  - daily_keywords (N rows)
  - product_rankings (N rows)

### Keyword Data (--keywords)
- Total records: N
- Period: YYYY-MM-DD ~ YYYY-MM-DD
- Unique keywords: N
- Recent top keywords:
  1. [keyword] (rank)

### Recommended Actions
- [Actions if issues found]
```

## Environment

- DATABASE_URL from: `/home/kkaemo/projects/naver-trend-intelligence/data_integration/api/.env`
- Expected connection: `postgresql://supabase_admin:***@172.17.0.1:54322/postgres`
