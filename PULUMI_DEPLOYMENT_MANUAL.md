# Complete Pulumi IaC Deployment Manual for OpenStack

This manual outlines the process to provision your cloud infrastructure on **OpenStack** and deploy the **Fulda Nexus App** (FastAPI Backend + React Frontend + MySQL Database + Nginx Reverse Proxy + Swift Assets Container) using Pulumi Infrastructure as Code (IaC).

---

## 🏗️ Architecture Overview

The infrastructure uses a secure, multi-tier layout:
- **Domain & Access**: Public traffic routes directly to the **Floating IP** associated with the primary **Web Server Instance**.
- **Compute (Web Servers)**: One or more scalable **Web Server Instances (Ubuntu, e.g. m1.small)** reside on the private network. They run **Docker & Docker Compose** to serve both the React frontend (compiled and hosted via Nginx proxy) and the FastAPI backend.
- **Compute (Database Server)**: A dedicated, private **Database Instance** running MySQL Server. It is isolated from the public internet by security group rules, allowing traffic *only* on port 3306 from the Web Server instances.
- **Storage**: An **OpenStack Swift Container** stores uploaded media and assets.

### 📊 Infrastructure Flow

```mermaid
graph TD
    Client[Client Browser] -->|HTTP:80 / HTTPS:443| FIP[Floating IP]
    FIP -->|Routes to Port 80| WebVM[Primary Web Server VM]
    
    subgraph Compute Tier (Scalable)
        WebVM --> Docker[Docker Compose]
        Docker --> Nginx[Nginx Container]
        Nginx -->|Serves| React[React Static Assets]
        Nginx -->|Proxies /api| FastAPI[FastAPI Backend Container]
    end

    FastAPI -->|Private Net:3306| DBVM[MySQL Database VM]
    FastAPI -->|Swift API| Swift[(Swift Container)]
    
    style DBVM fill:#f9f,stroke:#333,stroke-width:2px
    style Swift fill:#bbf,stroke:#333,stroke-width:2px
    style FIP fill:#bfb,stroke:#333,stroke-width:2px
```

---

## 📋 Prerequisites

Before initiating the deployment, ensure you have the following:

1. **Python 3.9+** and `pip`
2. **OpenStack CLI Credentials**: You must source your OpenStack RC file (containing `OS_AUTH_URL`, `OS_USERNAME`, `OS_PASSWORD`, `OS_PROJECT_NAME`, etc.) in your terminal.
3. **Pulumi CLI** (Install instructions at [pulumi.com](https://www.pulumi.com/docs/get-started/install/))
4. **Git**
5. An active SSH key pair created in your OpenStack dashboard (e.g., `fulda-key`).

---

## ⚙️ Configuration & Variables

Pulumi relies on configuration values managed in a stack file (`Pulumi.dev.yaml` or similar).

### 1. Configure the Python Virtual Environment
Navigate to the `infra` directory, set up a virtual environment, and install dependencies:

```bash
cd infra
python -m venv venv

# For Windows Powershell:
.\venv\Scripts\Activate.ps1

# For macOS/Linux:
source venv/bin/activate

# Install requirements (includes pulumi-openstack)
pip install -r requirements.txt
```

### 2. Initialize a Pulumi Stack
If you haven't initialized a stack yet, run:
```bash
pulumi stack init dev
```

### 3. Set Stack Configuration Variables
Define the configurations for your OpenStack environment. **Always write the database password as a secret!**

| Config Name | Type | Description | Default / Example |
| :--- | :--- | :--- | :--- |
| `key_name` | String | OpenStack SSH Key Pair Name | `CloudComp13-keypair` |
| `flavor_name` | String | OpenStack compute instance flavor size | `m1.small` |
| `image_name` | String | OpenStack Ubuntu OS image name | `ubuntu-22.04-jammy-server-cloud-image-amd64` |
| `external_network_name` | String | Name of the pre-existing external network | `ext_net` |
| `db_username` | String | Master DB user name | `fulda_user` |
| `db_password` | Secret | Master DB password (encrypted in stack file) | *User-defined* |
| `db_name` | String | Initial database name | `fulda_app` |
| `instance_count` | Int | Number of web servers to deploy (Elasticity) | `1` |

#### Commands to set configurations:
```bash
# Note: Key name, image name, and external network default to the verified student settings automatically.
# You can customize them or just run:
pulumi config set db_username fulda_user
pulumi config set db_name fulda_app
pulumi config set --secret db_password "YourSuperSecurePasswordHere123!"
pulumi config set instance_count 1
```

---

## 🚀 Execution & Deployment

### Step 1: Source your OpenStack Environment Credentials
Make sure your terminal has the OpenStack credentials exported:
```bash
# Example (macOS/Linux)
source project-openrc.sh

# Example (Windows Powershell)
$env:OS_AUTH_URL="https://private-cloud.informatik.hs-fulda.de:5000/v3"
$env:OS_USERNAME="CloudComp13"
$env:OS_PASSWORD="Hulk@3000"
$env:OS_PROJECT_NAME="CloudComp13"
$env:OS_USER_DOMAIN_NAME="Default"
$env:OS_PROJECT_DOMAIN_NAME="Default"
$env:OS_IDENTITY_API_VERSION="3"
```

### Step 2: Preview the Infrastructure Changes
Generate a dry-run execution plan:
```bash
pulumi preview
```

### Step 3: Deploy the Infrastructure
Apply the execution plan to provision the resources on OpenStack:
```bash
pulumi up
```
*Review the summary and type `yes` to confirm the deployment.*

### Step 4: Note the Stack Outputs
Once the deployment finishes successfully, Pulumi will print the stack outputs. Save these values:
* `Web_Primary_Public_IP`: The public Floating IP of your primary web server.
* `DB_Private_IP`: The private network IP address of your MySQL instance.
* `Swift_Container_Name`: The automatically generated Swift bucket/container name.
* `Web_Private_IPs`: The private IP list of all deployed web instances.

---

## 📦 App Deployment on Web Server VM

Now that your OpenStack infrastructure is active, you must configure the primary web instance and run the dockerized services.

### Step 1: Connect to the Primary Web Server via SSH
Using your OpenStack `.pem` private key:
```bash
chmod 400 fulda-key.pem
ssh -i fulda-key.pem ubuntu@<Web_Primary_Public_IP>
```

### Step 2: Clone the Project Repository
```bash
git clone https://github.com/YourOrganization/Fulda-Fall-2025-Team2.git app
cd app
```

### Step 3: Create Environment Configuration Files
You must supply `.env` files for both the backend container and the frontend proxy.

#### 1. Backend Configuration (`Backend/.env`)
Create the file:
```bash
nano Backend/.env
```
Copy and fill the values (adapting from [Backend/env.example](file:///c:/Users/darsh/Desktop/Fulda-Fall-2025-Team2-main/Fulda-Fall-2025-Team2-main/Backend/env.example)):
```ini
# Database (Connects to private MySQL VM Instance)
DATABASE_HOST=<DB_Private_IP_from_pulumi_output>
DATABASE_PORT=3306
DATABASE_NAME=fulda_app
DATABASE_USER=fulda_user
DATABASE_PASSWORD=<db_password_set_in_pulumi>
DATABASE_URL=mysql+asyncmy://fulda_user:<db_password>@<DB_Private_IP>:3306/fulda_app

# Security
SECRET_KEY=generate-a-long-random-string-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# API Configuration
API_V1_STR=/api/v1
PROJECT_NAME="Fulda Nexus API"

# CORS Allowed Origins
BACKEND_CORS_ORIGINS=["http://localhost", "http://<Web_Primary_Public_IP>"]

# Admin Startup Seeding
ADMIN_EMAIL=admin@informatik.hs-fulda.de
ADMIN_PASSWORD=ChangeMeOnFirstLogin!123
ADMIN_FIRST_NAMES=Fulda
ADMIN_LAST_NAME=Admin
ADMIN_DOB=1990-01-01

# Swift storage connection parameters (Configure if your backend connects to Swift API)
# S3_BUCKET_NAME=<Swift_Container_Name_from_pulumi_output>
```

### Step 4: Run the Application Stack
Execute Docker Compose using the root configuration file:
```bash
docker-compose up --build -d
```

### Step 5: Initialize DB Migrations & Database Seeding
```bash
# Verify containers are running
docker ps

# Run Alembic migrations
docker exec fastapi-backend alembic upgrade head

# Run the Demo Event Seeder script manually
docker exec -e PYTHONPATH=/app fastapi-backend python scripts/seed_events.py
```

---

## 🛑 Clean Up / Tearing Down

If you need to destroy the OpenStack resources to avoid resource usage:
```bash
pulumi destroy
```
*Confirm with `yes` to teardown all resources on OpenStack.*
