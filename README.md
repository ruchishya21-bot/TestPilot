@'
# TestPilot
### Automated Software Testing & Quality Assurance Framework

TestPilot is a Python-based automated testing and quality assurance platform designed to execute, monitor, analyze, and report software testing activities through a centralized web dashboard.

It combines automated functional testing, API validation, database testing, Selenium UI automation, performance testing, security checks, and test analytics into one platform.

---

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
- HTML and Allure test reports
- Parallel test execution

### 3. Quality Analytics
- Test execution statistics
- Failure analysis
- Historical run comparison
- Flaky test detection
- Retry tracking
- Coverage monitoring

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
- Coverage quality gate
- HTML test report artifacts
- CI execution logs

---

## Technology Stack

| Category | Technologies |
|---|---|
| Programming Language | Python |
| Backend | Flask |
| Testing | Pytest |
| UI Automation | Selenium WebDriver |
| API Testing | Requests |
| Database | SQLite |
| Test Reporting | Pytest HTML, Allure |
| Parallel Execution | Pytest-xdist |
| Coverage | Pytest-cov |
| Performance Testing | ThreadPoolExecutor, Requests |
| Frontend | HTML, CSS, JavaScript |
| CI/CD | GitHub Actions |
| Version Control | Git, GitHub |

---

## Project Structure

```text
TestPilot/
│
├── application/
│   ├── routes/
│   │   ├── qa.py
│   │   ├── flaky.py
│   │   ├── performance.py
│   │   └── security.py
│   │
│   ├── templates/
│   │   ├── dashboard.html
│   │   ├── flaky_dashboard.html
│   │   ├── performance_dashboard.html
│   │   └── security_dashboard.html
│   │
│   └── app.py
│
├── config/
│   └── target_config.py
│
├── tests/
│   ├── api/
│   ├── functional/
│   ├── ui/
│   ├── database/
│   ├── test_performance_routes.py
│   ├── test_security_routes.py
│   └── test_security_access.py
│
├── utilities/
│   ├── performance_tester.py
│   ├── security_tester.py
│   ├── flaky_tracker.py
│   └── result_store.py
│
├── reports/
├── screenshots/
├── .github/
│   └── workflows/
│       └── tests.yml
│
├── requirements.txt
├── pytest.ini
├── run_security_scan.py
└── README.md