# Refactor Skill

Code refactoring execution skill. Performs common base extraction, pattern integration, and standardization.

## Usage

```
/refactor [target] [options]
```

## Targets

- `clients` - API client integration
- `singleton` - Singleton pattern integration
- `errors` - Error handling standardization
- `logging` - Logging consistency
- `app` - app.py splitting

## Options

- `--dry-run` - Output plan without making changes
- `--backup` - Create backup before proceeding

## Instructions

You are a Code Refactoring Specialist. When this skill is invoked:

### 1. API Client Integration (`/refactor clients`)

**Current structure:**
```
api/
├── naver_client.py
├── naver_shopping_client.py
├── naver_ad_client.py
├── naver_commerce_client.py
├── weather_client.py
└── keyword_db_client.py
```

**Target structure:**
```
api/clients/
├── __init__.py
├── base_client.py        # Common HTTP/auth logic
├── naver_datalab.py
├── naver_shopping.py
├── naver_ad.py
├── naver_commerce.py
├── weather.py
└── keyword_db.py
```

**base_client.py template:**
```python
from abc import ABC, abstractmethod
import os
import logging
import requests
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class BaseAPIClient(ABC):
    """Base class for API clients"""

    def __init__(self):
        self._configure()

    @abstractmethod
    def _configure(self):
        """Client-specific configuration"""
        pass

    def _request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict] = None,
        data: Optional[Dict] = None,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """Common HTTP request"""
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers or self._get_headers(),
                json=data,
                timeout=timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            return self._get_fallback_response(e)

    @abstractmethod
    def _get_headers(self) -> Dict[str, str]:
        """Auth headers"""
        pass

    @abstractmethod
    def _get_fallback_response(self, error: Exception) -> Dict[str, Any]:
        """Fallback response on error"""
        pass
```

### 2. Singleton Pattern Integration (`/refactor singleton`)

**Create file:** `api/utils/singleton.py`

```python
from functools import wraps
from typing import TypeVar, Type

T = TypeVar('T')

def singleton(cls: Type[T]) -> Type[T]:
    """Singleton decorator"""
    instances = {}

    @wraps(cls)
    def get_instance(*args, **kwargs) -> T:
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance
```

**Usage:**
```python
from utils.singleton import singleton

@singleton
class NaverDataLabClient(BaseAPIClient):
    ...
```

### 3. Error Handling Standardization (`/refactor errors`)

**Create file:** `api/middleware/error_handler.py`

```python
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

class APIError(Exception):
    def __init__(self, message: str, status_code: int = 500, details: dict = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}

async def api_error_handler(request: Request, exc: APIError):
    logger.error(f"API Error: {exc.message}", extra=exc.details)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "message": exc.message,
            "details": exc.details
        }
    )

async def generic_error_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "Internal server error"
        }
    )
```

### 4. Logging Standardization (`/refactor logging`)

**Create file:** `api/utils/logging_config.py`

```python
import logging
import sys
from typing import Optional

def setup_logger(
    name: str,
    level: int = logging.INFO,
    format_string: Optional[str] = None
) -> logging.Logger:
    """Create standardized logger"""

    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(format_string))
        logger.addHandler(handler)

    return logger

# Sensitive data filter
class SensitiveDataFilter(logging.Filter):
    SENSITIVE_KEYS = ['password', 'api_key', 'secret', 'token']

    def filter(self, record):
        if hasattr(record, 'msg'):
            for key in self.SENSITIVE_KEYS:
                if key in str(record.msg).lower():
                    record.msg = "[REDACTED]"
        return True
```

### 5. app.py Splitting (`/refactor app`)

**Splitting plan:**
1. Config → `config.py`
2. Keyword endpoints → `routes/keywords.py`
3. Trend endpoints → `routes/trends.py`
4. Admin endpoints → `routes/admin.py`
5. Error handlers → `middleware/error_handler.py`

## Output Format

```
## Refactoring Report

### Changes
- [file] Change description

### Created Files
- [path] Description

### Migration Required
- [file] Import path change required

### Test Command
```bash
python -c "from app import app; print('OK')"
```
```

## Project Context

- Base path: `/home/kkaemo/projects/naver-trend-intelligence/data_integration`
