# Complete Step-by-Step OpenStack Deployment Guide
### Fulda Fall 2025 — Cloud Computing (Team 13)

This guide documents the complete end-to-end setup, infrastructure provisioning, and application deployment process for the **Fulda Nexus App** on the **Fulda University OpenStack Cloud**. 

---

## 🏗️ Architecture Design & Components

Our infrastructure layout separates the web tier from the database tier for high security, scalability, and ease of maintenance:

```mermaid
graph TD
    Client[Client Browser] -->|HTTP:80 / HTTPS:443| FIP[Floating IP: 10.32.6.178]
    FIP -->|Maps to Port 80| Port[Web Network Port]
    Port --> WebVM[Web Server VM: 10.0.1.71]
    
    subgraph Public Tier (Docker Compose Containerization)
        WebVM --> Nginx[Nginx Proxy Container]
        Nginx -->|Serves Web Assets| React[React Static Client]
        Nginx -->|Proxies /api| FastAPI[FastAPI Backend Container]
    end

    subgraph Private Isolated Tier
        FastAPI -->|Private Net Port 3306| DBVM[MySQL Database VM: 10.0.1.123]
        FastAPI -->|Swift Protocol| Swift[(Swift Asset Storage)]
    end
    
    style DBVM fill:#ffccd5,stroke:#ff3366,stroke-width:2px
    style Swift fill:#e8f0fe,stroke:#4285f4,stroke-width:2px
    style FIP fill:#e6fffa,stroke:#319795,stroke-width:2px
```

*   **Public Gateway (Floating IP)**: Serves as the entrance. It translates public traffic onto the private Web Server network port.
*   **Web Server VM (Docker Host)**: Resides inside the private subnet. It runs the frontend React client and the FastAPI backend inside isolated Docker containers.
*   **MySQL Database VM**: Runs as a separate VM in the private subnet. It is completely isolated from the internet. Its security group allows access **only** from the Web Server VM on port 3306.
*   **OpenStack Swift Container**: Serves as the object storage container for saving static uploads/images.

---

## Phase 1: Local Machine Configuration (One-Time Setup)

### Step 1: Install Pulumi CLI
Pulumi is the Infrastructure as Code (IaC) engine used to provision all resources automatically.
*   **Windows (PowerShell)**:
    ```powershell
    winget install pulumi
    ```
*   *Why?* We use Pulumi to define resources in Python code instead of manually clicking buttons in the Horizon UI, making deployments 100% reproducible.

### Step 2: Configure a Local State Backend
By default, Pulumi wants to log into a cloud account. To avoid this and store configuration files locally:
```powershell
pulumi login --local
```
*   *Why?* It removes dependencies on external services. The configuration and state files are saved inside your local user folder (`~/.pulumi`).

### Step 3: Create & Authorize your SSH Key Pair on Horizon
1.  Log into your **OpenStack Horizon Dashboard** (`https://private-cloud.informatik.hs-fulda.de/horizon`).
2.  Navigate to **Compute** ➔ **Key Pairs** ➔ Click **Create Key Pair**.
3.  Choose Key Type: **SSH Key** and name it `fulda-key-new`.
4.  Download the generated private key file `fulda-key-new.pem`.
5.  Move the `.pem` file to your project's `infra/` folder.
    *   *Why?* Linux VMs require an SSH key pair to authenticate SSH logins. You cannot use passwords to SSH into these VMs.

### Step 4: Restrict Local SSH Key File Permissions (Windows Fix)
Windows files by default inherit permissions that allow other users on the system to read them. SSH requires private keys to be completely private to you.
Run these commands in PowerShell inside the `infra` folder:
```powershell
icacls.exe .\fulda-key-new.pem /inheritance:r
icacls.exe .\fulda-key-new.pem /grant:r "$($env:USERNAME):(F)"
```
*   *Why?* If permissions are not restricted, SSH will reject the key with a `Permissions for 'fulda-key-new.pem' are too open` error and abort the connection.

### Step 5: Setup the Python Virtual Environment
Navigate to the `infra` directory on your local machine and initialize the packages:
```powershell
cd "c:\Users\darsh\Desktop\Fulda-Fall-2025-Team2-main\Fulda-Fall-2025-Team2-main\infra"
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
*   *Why?* Isolates dependencies (like `pulumi-openstack`) from your system's global Python installation to prevent version conflicts.

---

## Phase 2: Pulumi Setup & Cloud Credentials

### Step 6: Set your Encryption Passphrase
Since we are using a local Pulumi backend, we must provide a password to encrypt sensitive stack variables (like the database password):
```powershell
$env:PULUMI_CONFIG_PASSPHRASE="Fulda2025"
```
*   *Why?* Instead of prompting you for a password on every command, setting this environment variable allows Pulumi to authenticate commands automatically.

### Step 7: Load OpenStack API Environment Variables
Before running Pulumi, configure your terminal to log into Keystone (OpenStack's Identity service) by running:
```powershell
$env:OS_AUTH_URL="https://private-cloud.informatik.hs-fulda.de:5000/v3"
$env:OS_USERNAME="CloudComp13"
$env:OS_PASSWORD="Hulk@3000"
$env:OS_PROJECT_NAME="CloudComp13"
$env:OS_USER_DOMAIN_NAME="Default"
$env:OS_PROJECT_DOMAIN_NAME="Default"
$env:OS_IDENTITY_API_VERSION="3"
$env:OS_INSECURE="true"
```
*   *Why?*
    *   `OS_AUTH_URL` points Pulumi directly to Keystone's authentication portal.
    *   `OS_INSECURE="true"` tells Pulumi to ignore security warnings for self-signed certificates, which are commonly used in academic labs.

### Step 8: Initialize and Select the Dev Stack
Initialize the environment configuration file (`Pulumi.dev.yaml`):
```powershell
pulumi stack init dev
# OR if it already exists:
pulumi stack select dev
```

### Step 9: Configure Project Secrets
Store variables that our Pulumi code uses inside the stack registry:
```powershell
pulumi config set db_username fulda_user
pulumi config set db_name fulda_app
pulumi config set --secret db_password "Hulk@3000"
pulumi config set key_name fulda-key-new
```
*   *Why?* The `--secret` flag encrypts your database password using the passphrase we set in Step 6, keeping it secure inside your version control system.

---

## Phase 3: Provisioning Infrastructure (IaC)

### Step 10: Run the Deployment
Deploy the configuration script defined in `__main__.py` to create the networks, security rules, storage, and VMs:
```powershell
pulumi up
```
*   *Why?* This command reads your Python infrastructure script, compiles it into a DAG (Directed Acyclic Graph), and provisions the resources in the exact correct order. Type `yes` when prompted.

#### 🛠️ What did Pulumi create under the hood?
1.  **VPC / Subnet**: Defined a private network (`fulda-network`) and subnet (`10.0.1.0/24`) with DNS set to `8.8.8.8` to let instances reach the external internet.
2.  **External Gateway Router**: Created `fulda-router` and linked it to the university's external network gateway (`ext_net`).
3.  **Firewall Rules (Security Groups)**:
    *   `fulda-secgroup-web`: Opens ports `22` (SSH), `80` (HTTP), and `443` (HTTPS).
    *   `fulda-secgroup-db`: Opens port `3306` (MySQL) but restricts source traffic **only** to members of `fulda-secgroup-web`.
4.  **MySQL Database VM (`fulda-db-server`)**:
    *   Provisioned an Ubuntu server using `user_data` boot-scripts to automatically install MySQL Server, bind it to all interfaces, create the database, and grant access permissions.
    *   *Dependency Check:* Added `opts=pulumi.ResourceOptions(depends_on=[subnet, router_interface])` to prevent boot errors before the network subnets were active.
5.  **Web Server VM (`fulda-web-server-0`)**:
    *   Provisioned an Ubuntu server.
    *   *Elasticity swap space:* Since compiling React apps requires significant memory, the startup script automatically creates a **2GB swap file** to prevent Out-Of-Memory (OOM) compilation crashes.
    *   Installed Docker & Docker Compose automatically.
6.  **Explicit Ports & Floating IP**:
    *   Instead of letting OpenStack dynamically assign interfaces, we declared an explicit `openstack.networking.Port` object for the Web VM.
    *   *Why?* Declaring the port explicitly in Pulumi allows us to reliably bind the public **Floating IP (`10.32.6.178`)** to the Web VM.

---

## Phase 4: Application Deployment & Seeding

### Step 11: Connect to your Web VM via SSH
Once the deployment finishes, use your SSH key to log into the public web server:
```powershell
ssh -i fulda-key-new.pem ubuntu@10.32.6.178
```

### Step 12: Clone the Git Repository
On the server terminal, clone the code:
```bash
git clone https://github.com/darshanpeddadad/CloudComputing-13.git app
cd app
```

### Step 13: Create the Environment Config File
Create the environment configuration:
```bash
nano Backend/.env
```
Paste this configuration inside:
```ini
DATABASE_HOST=10.0.1.123
DATABASE_PORT=3306
DATABASE_NAME=fulda_app
DATABASE_USER=fulda_user
DATABASE_PASSWORD=Hulk@3000
DATABASE_URL=mysql+asyncmy://fulda_user:Hulk%403000@10.0.1.123:3306/fulda_app
SECRET_KEY=fulda-super-secret-key-change-in-prod
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
API_V1_STR=/api/v1
PROJECT_NAME="Fulda Nexus API"
BACKEND_CORS_ORIGINS=["http://10.32.6.178"]
ADMIN_EMAIL=admin@informatik.hs-fulda.de
ADMIN_PASSWORD=ChangeMeOnFirstLogin!123
ADMIN_FIRST_NAMES=Fulda
ADMIN_LAST_NAME=Admin
ADMIN_DOB=1990-01-01
```
*   *Critical Fix:* The password contains an `@` symbol (`Hulk@3000`). Because `@` is the standard separator for URLs (`user:pass@host`), we **must URL-encode it as `%40`** in `DATABASE_URL` (`Hulk%403000`). Failing to do so causes a name resolution crash because the driver thinks the host is `3000@10.0.1.123`.

### Step 14: Boot the Application
Build and launch the containers:
```bash
docker-compose up --build -d
```
*   *Why?* The `-d` flag runs the containers in detached (background) mode, and `--build` compiles your static frontend assets inside Nginx.

### Step 15: Run Database migrations & Seeding
Once the containers are started, run the database setup commands:
```bash
# Run migrations to build the tables
docker exec -e PYTHONPATH=/app fastapi-backend alembic upgrade head

# Run the python seeder script to populate sample events
docker exec -e PYTHONPATH=/app fastapi-backend python scripts/seed_events.py
```
*   *Why?* Running docker commands with `-e PYTHONPATH=/app` overrides the default search path, allowing Python to discover custom workspace modules (such as your `app` schemas).

---

## Phase 5: Verification & Production Accessibility

Your application is now fully running. Since the university cloud is hosted on their internal campus network:

*   **To access it**: You must be on the **University Wi-Fi** or logged into the **University VPN**.
*   **Web Portal**: Open your browser and navigate to **[http://10.32.6.178](http://10.32.6.178)**.
*   **Backend API Documentation**: Open **[http://10.32.6.178/api/docs](http://10.32.6.178/api/docs)** to view the interactive FastAPI Swagger specs.
*   **System Health Check**: Go to **[http://10.32.6.178/api/health](http://10.32.6.178/api/health)**. It will query the database server privately and return:
    ```json
    {"status":"healthy"}
    ```
