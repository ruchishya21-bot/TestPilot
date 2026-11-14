from utilities.security_tester import run_security_scan

r = run_security_scan()

print("STATUS:", r["status"])
print("TOTAL CHECKS:", r["total_checks"])
print("PASSED:", r["passed"])
print("FAILED:", r["failed"])
print("WARNINGS:", r["warnings"])
print("RISK SCORE:", r["risk_score"])

for finding in r["findings"]:
    print(
        finding["severity"],
        "|", finding["status"],
        "|", finding["title"],
        "|", finding["description"]
    )
