# Fulda Nexus — Cloud Infrastructure & Deployment (OpenStack + Pulumi)

The application runs on a fully automated, secure, multi-tier environment on the **Fulda University OpenStack Cloud**, provisioned using **Pulumi Infrastructure as Code (IaC)**.

---

## Architecture

| Layer | Resource | Details |
|---|---|---|
| Network | Private Subnet | `10.0.1.0/24`, isolated with a dedicated router |
| Compute — Web | Ubuntu VM (Web Server) | Public Floating IP via `ext_net`, runs Docker + Nginx + FastAPI + React |
| Compute — DB | Ubuntu VM (DB Server) | Private-only, MySQL on port `3306`, accessible only from the web security group |
| Storage | Swift Object Container | `fulda-assets`, publicly readable for serving media |

Web instances include a **2 GB swap file** to prevent out-of-memory crashes during the React frontend build.

---

## Quick-Start Deployment

The entire provisioning and VM setup is handled by a single PowerShell script.

### 1. Prerequisites

- Pulumi CLI installed (`winget install Pulumi.Pulumi`)
- Python 3.9+ and `pip`
- SSH key `fulda-key-new.pem` placed inside the `infra/` directory

### 2. Set Up the Python Virtual Environment

```powershell
cd infra
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3. Initialize the Pulumi Stack (first time only)

```powershell
pulumi login --local
pulumi stack select dev --create
```

### 4. Run the Deployment Script

```powershell
.\deploy.ps1
```

This single command:
1. Loads OpenStack credentials via `setup-env.ps1`
2. Activates the Python virtual environment
3. Sets Pulumi secrets and runs `pulumi up --yes`
4. Waits for VM cloud-init to finish (Docker + git clone)
5. Writes the `.env` file to the web VM over SSH
6. Starts Docker Compose (`docker compose up --build -d`)
7. Polls for MySQL DB connectivity
8. Runs Alembic migrations and seeds the database

---

## Script Actions

| Command | Effect |
|---|---|
| `.\deploy.ps1` | Full deploy: provision infrastructure + configure VMs |
| `.\deploy.ps1 -Action vm-setup` | Re-configure VMs only (skips `pulumi up`) |
| `.\deploy.ps1 -Action destroy` | Tear down all OpenStack resources |

---

## Stack Outputs

After a successful deploy, Pulumi exports:

| Output | Description |
|---|---|
| `Web_Primary_Public_IP` | Public floating IP of the primary web server |
| `DB_Private_IP` | Private IP of the MySQL VM |
| `Web_Private_IPs` | Private IPs of all web instances |
| `Swift_Container_Name` | Name of the Swift object storage container |
| `Network_ID` / `Subnet_ID` / `Router_ID` | Network resource IDs |

---

## Live Endpoints

Once deployed, the app is reachable on the university intranet/VPN:

| Endpoint | URL |
|---|---|
| Frontend Portal | `http://<Web_Primary_Public_IP>` |
| Backend Swagger Docs | `http://<Web_Primary_Public_IP>/api/docs` |
| Health Check | `http://<Web_Primary_Public_IP>/api/health` |
