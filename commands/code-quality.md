# Code Quality Check Skill

Code quality inspection skill. Detects hardcoded values, duplicate patterns, and circular dependencies.

## Usage

```
/code-quality [path] [options]
```

## Options

- `--hardcoded` - Search for hardcoded values only
- `--duplicates` - Detect duplicate patterns only
- `--imports` - Check import circular dependencies only
- `--all` - Run all checks (default)

## Instructions

You are a Code Quality Analyst. When this skill is invoked:

### 1. Hardcoded Value Search

```bash
# Password/API key patterns
grep -rn "password\s*=\s*['\"]" $PATH --include="*.py"
grep -rn "api_key\s*=\s*['\"]" $PATH --include="*.py"
grep -rn "secret\s*=\s*['\"]" $PATH --include="*.py"

# Hardcoded URLs
grep -rn "http[s]*://[a-zA-Z0-9]" $PATH --include="*.py" | grep -v ".env"

# Hardcoded ports/IPs
grep -rn ":[0-9]\{4,5\}" $PATH --include="*.py"
grep -rn "[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}" $PATH --include="*.py"
```

### 2. Duplicate Pattern Detection

Singleton pattern duplicates:
```bash
grep -rn "_instance\s*=" $PATH --include="*.py"
grep -rn "def get_.*_client" $PATH --include="*.py"
```

Error handling pattern duplicates:
```bash
grep -rn "except Exception" $PATH --include="*.py"
grep -rn "except.*RequestException" $PATH --include="*.py"
```

### 3. Import Circular Dependency Check

```bash
# Check mutual imports
for file in $(find $PATH -name "*.py"); do
    imports=$(grep "^from\|^import" $file | grep -v "__future__")
    echo "=== $file ==="
    echo "$imports"
done
```

### 4. Test Coverage Check

```bash
# Check test file existence
find $PATH -name "test_*.py" -o -name "*_test.py"

# Run pytest (if available)
cd $PATH && pytest --cov --cov-report=term-missing 2>/dev/null || echo "pytest not installed"
```

## Output Format

```
## Code Quality Report

### Hardcoded Values
- [file:line] Detected pattern

### Duplicate Patterns
- [pattern type] Detected locations

### Import Issues
- [file] Circular dependency candidates

### Test Coverage
- Test file count: N
- Coverage: N%

### Recommended Actions
1. [priority] Action item
```

## Project Context

- Main project: `/home/kkaemo/projects/naver-trend-intelligence/data_integration`
- Main inspection targets: `api/`, `cross_module/`, `ai/`, `forecasting/`
