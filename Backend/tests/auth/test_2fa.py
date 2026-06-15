from fastapi.testclient import TestClient
import pyotp

from Backend.tests.auth.utils import auth_url, login_payload, registration_payload

def test_2fa_full_flow(client: TestClient):
    # 1. Register and Login
    password = "SecurePass1!"
    email = registration_payload()["email"]
    client.post(
        auth_url("/register"),
        json=registration_payload(email=email, password=password),
    )
    
    login_resp = client.post(auth_url("/login"), json=login_payload(email=email, password=password))
    assert login_resp.status_code == 200
    access_token = login_resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    # 2. Enable 2FA
    enable_resp = client.post(auth_url("/2fa/enable"), headers=headers)
    assert enable_resp.status_code == 200
    enable_data = enable_resp.json()["data"]
    secret = enable_data["secret"]
    assert secret
    assert enable_data["qr_code"]

    # 3. Verify OTP
    totp = pyotp.TOTP(secret)
    code = totp.now()
    verify_resp = client.post(
        auth_url("/2fa/verify"), 
        headers=headers,
        json={"code": code}
    )
    assert verify_resp.status_code == 200
    assert len(verify_resp.json()["data"]["backup_codes"]) == 10

    # 4. Login with 2FA
    # Step 1: Password login returns 2fa_required signal
    login_step1 = client.post(auth_url("/login"), json=login_payload(email=email, password=password))
    assert login_step1.status_code == 200
    step1_data = login_step1.json()
    
    assert step1_data["data"].get("two_factor_required") is True
    temp_token = step1_data["data"].get("temp_token")
    assert temp_token

    # Step 2: Complete login with OTP code
    code_login = totp.now()
    login_step2 = client.post(
        auth_url("/2fa/login"),
        json={"temp_token": temp_token, "code": code_login}
    )
    assert login_step2.status_code == 200
    final_data = login_step2.json()["data"]
    assert final_data["access_token"]
    assert final_data["user"]["email"] == email

def test_2fa_fails_with_invalid_code(client: TestClient):
    # Setup user with 2FA
    password = "SecurePass1!"
    email = registration_payload()["email"]
    client.post(auth_url("/register"), json=registration_payload(email=email, password=password))
    login_resp = client.post(auth_url("/login"), json=login_payload(email=email, password=password))
    token = login_resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Enable
    enable_data = client.post(auth_url("/2fa/enable"), headers=headers).json()["data"]
    secret = enable_data["secret"]
    totp = pyotp.TOTP(secret)
    client.post(auth_url("/2fa/verify"), headers=headers, json={"code": totp.now()})

    # Try login with bad code
    login_step1 = client.post(auth_url("/login"), json=login_payload(email=email, password=password))
    temp_token = login_step1.json()["data"]["temp_token"]

    login_step2 = client.post(
        auth_url("/2fa/login"),
        json={"temp_token": temp_token, "code": "000000"}
    )
    assert login_step2.status_code == 401
