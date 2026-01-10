# Test Generation Skill

Automatic test code generation skill. Generates pytest-based tests.

## Usage

```
/test-gen [target] [options]
```

## Targets

- `api` - API endpoint tests
- `client` - Client tests
- `module` - Module unit tests
- Or specific file path

## Options

- `--coverage` - Specify coverage target (default 80%)
- `--mock` - Use mocks (enabled by default)
- `--fixtures` - Generate fixtures only

## Instructions

You are a Test Engineer. When this skill is invoked:

### 1. API Endpoint Test Generation

**Template:** `tests/test_[route_name].py`

```python
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

from app import app

client = TestClient(app)


class TestInsightsAPI:
    """Insights API tests"""

    def test_get_insights_success(self):
        """Normal query test"""
        response = client.get("/api/insights")
        assert response.status_code == 200
        assert "status" in response.json()

    def test_get_insights_with_params(self):
        """Query with parameters"""
        response = client.get("/api/insights?limit=10&offset=0")
        assert response.status_code == 200

    def test_get_insights_invalid_params(self):
        """Invalid parameters"""
        response = client.get("/api/insights?limit=-1")
        assert response.status_code == 422  # Validation error

    @patch('dependencies.get_integration_service')
    def test_get_insights_service_error(self, mock_service):
        """Service error handling"""
        mock_service.return_value.get_insights.side_effect = Exception("DB Error")
        response = client.get("/api/insights")
        assert response.status_code == 500


class TestInsightsAI:
    """AI insights tests"""

    @pytest.fixture
    def mock_ai_client(self):
        with patch('ai.gemini_client.GeminiClient') as mock:
            mock.return_value.is_available.return_value = True
            mock.return_value.analyze_trend.return_value = {"status": "success"}
            yield mock

    def test_generate_ai_insight(self, mock_ai_client):
        """AI insight generation"""
        response = client.post("/api/insights/generate-ai")
        assert response.status_code in [200, 503]
```

### 2. Client Test Generation

**Template:** `tests/test_clients/test_[client_name].py`

```python
import pytest
from unittest.mock import patch, MagicMock
import requests

from clients.naver_datalab import NaverDataLabClient


class TestNaverDataLabClient:
    """Naver DataLab client tests"""

    @pytest.fixture
    def client(self):
        with patch.dict('os.environ', {
            'NAVER_DATALAB_CLIENT_ID': 'test_id',
            'NAVER_DATALAB_CLIENT_SECRET': 'test_secret'
        }):
            return NaverDataLabClient()

    @pytest.fixture
    def mock_response(self):
        mock = MagicMock()
        mock.status_code = 200
        mock.json.return_value = {"result": "success"}
        return mock

    def test_client_initialization(self, client):
        """Initialization test"""
        assert client.client_id == 'test_id'
        assert client.client_secret == 'test_secret'

    @patch('requests.request')
    def test_get_trend_success(self, mock_request, client, mock_response):
        """Trend query success"""
        mock_request.return_value = mock_response
        result = client.get_trend("keyword")
        assert result is not None

    @patch('requests.request')
    def test_get_trend_api_error(self, mock_request, client):
        """API error handling"""
        mock_request.side_effect = requests.exceptions.RequestException("API Error")
        result = client.get_trend("keyword")
        # Check mock data return
        assert result is not None
```

### 3. Fixture Generation

**Template:** `tests/conftest.py`

```python
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from app import app


@pytest.fixture
def test_client():
    """FastAPI test client"""
    return TestClient(app)


@pytest.fixture
def mock_db_connection():
    """DB connection mock"""
    mock = MagicMock()
    mock.cursor.return_value.__enter__ = MagicMock()
    mock.cursor.return_value.__exit__ = MagicMock()
    return mock


@pytest.fixture
def sample_keyword_data():
    """Sample keyword data"""
    return [
        {"keyword": "summer dress", "rank": 1, "scrape_date": "2025-01-10"},
        {"keyword": "mens jacket", "rank": 2, "scrape_date": "2025-01-10"},
    ]


@pytest.fixture
def sample_forecast_result():
    """Sample forecast result"""
    return {
        "keyword": "summer dress",
        "current_rank": 10,
        "predicted_rank": 5,
        "expected_trend": "up",
        "confidence": 0.85
    }


@pytest.fixture
def mock_integration_service():
    """IntegrationService mock"""
    mock = MagicMock()
    mock.get_insights.return_value = {"insights": []}
    mock.get_correlations.return_value = {"correlations": []}
    return mock
```

### 4. Integration Test Generation

**Template:** `tests/integration/test_pipeline.py`

```python
import pytest
from unittest.mock import patch

class TestPipeline:
    """Integration pipeline tests"""

    @pytest.mark.integration
    def test_full_pipeline(self):
        """Full pipeline test"""
        # 1. Data collection
        # 2. Forecast execution
        # 3. AI analysis
        # 4. Slack notification
        pass

    @pytest.mark.integration
    def test_forecast_to_slack(self):
        """Forecast → Slack pipeline"""
        pass
```

## Output Format

```
## Test Generation Report

### Generated Tests
- [file] Test class/method count

### Required Fixtures
- [name] Purpose

### Run Commands
```bash
pytest tests/ -v
pytest tests/ --cov --cov-report=html
```

### Expected Coverage
- [module] N%
```

## Project Context

- Test directory: `/home/kkaemo/projects/naver-trend-intelligence/data_integration/api/tests`
- Framework: pytest
- Mock: unittest.mock
