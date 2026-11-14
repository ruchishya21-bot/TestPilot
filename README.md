# TestPilot
### Automated Software Testing & Quality Assurance Framework

TestPilot is a Python-based automated testing and quality assurance platform that brings functional testing, API validation, database testing, browser automation, performance testing, and security assessment together in a centralized web dashboard.

It provides test execution management, historical analytics, failure tracking, flaky test detection, and continuous integration through GitHub Actions.

## Key Features

### 1. Automated Testing
- API endpoint testing
- Functional and regression testing
- Database validation
- Selenium-based UI automation
- Page Object Model architecture
- Data-driven test execution

### 2. Test Execution Management
- Centralized test execution
- Persistent execution history
- Test result tracking
- Failure screenshots
- HTML and Allure reporting
- Parallel test execution

### 3. Quality Analytics
- Test execution statistics
- Failure analysis
- Historical run comparison
- Flaky test detection
- Retry tracking
- Code coverage monitoring

### 4. Performance Testing
- Configurable API load testing
- Concurrent request execution
- Response-time measurements
- Throughput analysis
- P50, P95, and P99 latency metrics
- Historical performance analytics

### 5. Security Testing
- HTTP security header inspection
- Session cookie security assessment
- Authentication enforcement checks
- API access-control validation
- Sensitive resource exposure checks
- Basic SQL injection error probing
- Basic reflected XSS probing
- Security risk scoring
- Persistent security scan history

### 6. Interactive Dashboard
- Flask-powered web interface
- Dedicated testing and analytics dashboards
- Execution history and statistics
- Performance monitoring
- Security findings and scan history
- Automatic dashboard data refresh

### 7. CI/CD Integration
- GitHub Actions workflow
- Automated test execution
- Parallel testing
- Code coverage quality gate
- HTML test report artifacts
- CI execution logs

## Technology Stack

| Category | Technologies |
|---|---|
| Programming Language | Python |
| Backend | Flask |
| Testing Framework | Pytest |
| UI Automation | Selenium WebDriver |
| API Testing | Requests |
| Database | SQLite |
| Reporting | Pytest HTML, Allure |
| Parallel Execution | Pytest-xdist |
| Coverage | Pytest-cov |
| Performance Testing | ThreadPoolExecutor, Requests |
| Frontend | HTML, CSS, JavaScript |
| CI/CD | GitHub Actions |
| Version Control | Git, GitHub |

## Project Structure

```text
TestPilot/
│
├── application/
│   ├── database/
│   │   ├── db.py
│   │   └── schema.sql
│   │
│   ├── routes/
│   │   ├── auth.py
│   │   ├── flasky.py
│   │   ├── performance.py
│   │   ├── qa.py
│   │   └── security.py
│   │
│   ├── templates/
│   ├── static/
│   └── app.py
│
├── config/
│   └── target_config.py
│
├── test_data/
│   └── target_endpoints.json
│
├── tests/
│   ├── api/
│   ├── database/
│   ├── data_driven/
│   ├── functional/
│   ├── target/
│   ├── ui/
│   ├── test_app_routes.py
│   ├── test_performance_routes.py
│   ├── test_security_access.py
│   └── test_security_routes.py
│
├── utilities/
│   ├── execution_manager.py
│   ├── flaky_tracker.py
│   ├── performance_tester.py
│   ├── result_store.py
│   ├── security_tester.py
│   └── target_validator.py
│
├── .github/
│   └── workflows/
│       └── tests.yml
│
├── requirements.txt
├── pytest.ini
├── run_security_scan.py
└── README.md
```

## Installation and Setup

### Prerequisites

- Python 3.10 or later
- Git
- Google Chrome or another supported browser for Selenium UI tests

### 1. Clone the Repository

```bash
git clone https://github.com/ruchishya21-bot/TestPilot.git
cd TestPilot
```

### 2. Create a Virtual Environment

Windows PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Running the Application

Start the Flask application:

```powershell
python -m flask --app application.app run --host 127.0.0.1 --port 5000
```

Open the application in your browser:

```text
http://127.0.0.1:5000
```

Register an account and log in to access the testing and analytics dashboards.

Health endpoint:

```text
http://127.0.0.1:5000/health
```

Keep the Flask application running while executing integration and UI tests that interact with the application.

## Configuration

TestPilot uses environment variables to configure the target application.

| Variable | Default | Description |
|---|---|---|
| `TESTPILOT_APP_NAME` | TestPilot Demo Application | Target application name |
| `TESTPILOT_BASE_URL` | `http://127.0.0.1:5000` | Target application URL |
| `TESTPILOT_HEALTH_ENDPOINT` | `/health` | Target health endpoint |
| `TESTPILOT_REQUEST_TIMEOUT` | `15` | HTTP request timeout in seconds |
| `TESTPILOT_HEADLESS` | `false` | Enable headless browser execution |
| `TESTPILOT_SECRET_KEY` | Development fallback | Flask session secret |
| `TESTPILOT_COOKIE_SECURE` | `false` | Enable secure session cookies |

Example PowerShell configuration:

```powershell
$env:TESTPILOT_BASE_URL = "http://127.0.0.1:5000"
$env:TESTPILOT_HEADLESS = "true"
$env:TESTPILOT_REQUEST_TIMEOUT = "15"
```

For production deployments, configure a strong secret key, disable Flask debug mode, use HTTPS, and enable secure cookies.

## Running Tests

Run the complete test suite:

```powershell
pytest tests
```

Run tests in parallel:

```powershell
pytest tests -n 2
```

Run tests with the coverage quality gate:

```powershell
pytest tests -n 2 --cov-fail-under=90 --cov=application --cov-report=term-missing
```

Generate an HTML test report:

```powershell
pytest tests --html=reports/report.html --self-contained-html
```

Generate Allure test results:

```powershell
pytest tests --alluredir=reports/allure-results
```

Generate HTML coverage reports:

```powershell
pytest tests --cov=application --cov-report=html:reports/coverage
```

## Security Assessment

TestPilot includes automated security checks for HTTP headers, authentication enforcement, API access control, sensitive resource exposure, session cookie attributes, and basic injection-related indicators.

Security scans can be executed using the security dashboard.

**Security testing limitation:** These checks provide a basic automated security assessment. They do not replace professional penetration testing, comprehensive vulnerability scanning, or a dedicated security audit.

Only run security assessments against applications you own or are explicitly authorized to test.

## Continuous Integration

TestPilot uses GitHub Actions to automate quality checks.

The CI pipeline:
1. Checks out the repository.
2. Sets up Python.
3. Installs project dependencies.
4. Starts the Flask application.
5. Executes automated tests in parallel.
6. Enforces the minimum 90% code coverage requirement.
7. Uploads test reports and coverage artifacts.

Workflow configuration:

```text
.github/workflows/tests.yml
```

## Reporting and Analytics

TestPilot provides:
- Automated test execution reports
- Historical execution records
- Failure analysis
- Flaky test analytics
- Performance metrics and trends
- Security findings and scan history
- Code coverage reports

## Future Enhancements

Potential areas for future development include:
- Expanded vulnerability detection
- Additional performance-testing strategies
- Advanced test analytics
- More CI/CD integrations
- Extended browser and cross-platform testing

## Author

**Ruchishya**

GitHub: https://github.com/ruchishya21-bot

---

TestPilot — Bringing automated testing, quality analytics, performance assessment, and security checks into one platform.