import requests

login_url = "http://127.0.0.1:8000/api/auth/login"
dashboard_url = "http://127.0.0.1:8000/api/candidate/dashboard"

resp = requests.post(login_url, json={"email": "candidate@intellihire.dev", "password": "TestCandidate123!"})
print("Login status:", resp.status_code)
if resp.status_code == 200:
    token = resp.json().get("data", {}).get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    dashboard_resp = requests.get(dashboard_url, headers=headers)
    print("Dashboard status:", dashboard_resp.status_code)
    print("Dashboard body:", dashboard_resp.text)
else:
    print("Login body:", resp.text)
