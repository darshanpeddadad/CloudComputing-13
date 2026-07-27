# Complete Step-by-Step Deployment Tutorial: Fulda Nexus App
### Fulda Fall 2025 — Cloud Computing Infrastructure & Application Deployment

This tutorial provides a complete, foolproof, end-to-end guide to deploying the **Fulda Nexus App** on the **Fulda University OpenStack Cloud** using **Pulumi Infrastructure as Code (IaC)** and **Docker Compose**. 

It is designed so that a teammate or friend can clone this repository, use the same credentials, and run the exact same setup on their local machine to achieve a fully running deployment.

---

## 🏗️ System Architecture & Flow

Before running commands, it is essential to understand what we are building. The system separates the web presentation/application layer from the database storage layer for high security and performance:

```mermaid
graph TD
    Client[Client Browser] -->|HTTP:80 / HTTPS:443| FIP[Floating IP: 10.32.6.178]
    FIP -->|Routes to Port 80| Port[Web Network Port]
    Port --> WebVM[Web Server VM: 10.0.1.x]
    
    subgraph Public Tier (Docker Compose Containerization)
        WebVM --> Nginx[Nginx Proxy Container]
        Nginx -->|Serves Web Assets| React[React Static Client]
        Nginx -->|Proxies /api| FastAPI[FastAPI Backend Container]
    end

    subgraph Private Isolated Tier
        FastAPI -->|Private Net Port 3306| DBVM[MySQL Database VM: 10.0.1.x]
        FastAPI -->|Swift Protocol| Swift[(Swift Asset Storage)]
    end
    
    style DBVM fill:#ffccd5,stroke:#ff3366,stroke-width:2px
    style Swift fill:#e8f0fe,stroke:#4285f4,stroke-width:2px
    style FIP fill:#e6fffa,stroke:#319795,stroke-width:2px
```

*   **Public Gateway (Floating IP)**: The external entry point. Public internet traffic hits the Floating IP, which maps to the Web Server VM's internal port.
*   **Web Server VM**: Runs the React frontend and FastAPI backend inside isolated Docker containers using a bridge network. It has a **2GB swap space** file initialized during boot to prevent Out-of-Memory (OOM) errors during the React asset building phase.
*   **Database VM**: Completely isolated from the internet. Its security group allows access **only** from the Web Server VM on port 3306.
*   **Swift Storage**: Object storage container for user-uploaded assets/files.

---

## 📋 Table of Contents
1. [Phase 1: Local Machine Prerequisites](#phase-1-local-machine-prerequisites)
2. [Phase 2: SSH Key Setup & Directory Setup](#phase-2-ssh-key-setup--directory-setup)
3. [Phase 3: Sourcing Cloud Credentials](#phase-3-sourcing-cloud-credentials)
4. [Phase 4: Local Pulumi Setup & Stack Configuration](#phase-4-local-pulumi-setup--stack-configuration)
5. [Phase 5: Deploying Cloud Infrastructure (IaC)](#phase-5-deploying-cloud-infrastructure-iac)
6. [Phase 6: SSH Connecting & Deploying the Application Stack](#phase-6-ssh-connecting--deploying-the-application-stack)
7. [Phase 7: Database Seeding & Migration](#phase-7-database-seeding--migration)
8. [Phase 8: Accessing and Verifying the Deployment](#phase-8-accessing-and-verifying-the-deployment)
9. [Phase 9: Tearing Down Infrastructure](#phase-9-tearing-down-infrastructure)

---

## Phase 1: Local Machine Prerequisites

Your friend must install the following software tools on their computer to compile and manage the deployment:

### 1. Python 3.9+ & pip
*   **Purpose**: Pulumi compiles our infrastructure blueprint written in Python (`__main__.py`).
*   **Verification Command**:
    ```bash
    python --version
    pip --version
    ```

### 2. Git
*   **Purpose**: Used to pull codebase updates.
*   **Verification Command**:
    ```bash
    git --version
    ```

### 3. Pulumi CLI
*   **Purpose**: The main orchestration tool that translates Python scripts into OpenStack API commands and tracks resource status.
*   **Installation (Windows PowerShell)**:
    ```powershell
    winget install Pulumi.Pulumi
    ```
*   **Installation (macOS via Homebrew)**:
    ```bash
    brew install pulumi
    ```
*   **Installation (Linux)**:
    ```bash
    curl -fsSL https://get.pulumi.com | sh
    ```
*   **Reload Path**: Restart your terminal or reload environment paths, then verify:
    ```bash
    pulumi version
    ```

---

## Phase 2: SSH Key Setup & Directory Setup

Linux virtual machines require a private/public keypair to authorize SSH connections.

### 1. Download/Create your SSH Private Key
*   You must obtain the private key file **`fulda-key-new.pem`** (downloaded from OpenStack Horizon under **Compute -> Key Pairs**).
*   Save this file inside the `infra/` directory of the project.

### 2. Restrict File Permissions (CRITICAL STEP)
SSH clients will reject your connection if the private key file permissions are too open (i.e. if other OS users can read it).

#### 🔒 Windows (PowerShell):
Run these commands inside the `infra` folder to disable inheritance and grant full control only to your logged-in username:
```powershell
# Navigate to infra folder
cd "c:\Users\darsh\Desktop\Fulda-Fall-2025-Team2-main\Fulda-Fall-2025-Team2-main\infra"

# Remove inherited permissions and grant explicit full control to the current user
icacls.exe .\fulda-key-new.pem /inheritance:r
icacls.exe .\fulda-key-new.pem /grant:r "$($env:USERNAME):(F)"
```

#### 🔒 macOS / Linux (Terminal):
```bash
cd infra/
chmod 400 fulda-key-new.pem
```

---

## Phase 3: Sourcing Cloud Credentials

Pulumi needs authentication tokens to talk to the OpenStack Horizon server.

Set these environment variables in your terminal session before launching Pulumi.

#### 🔑 Windows (PowerShell):
Run these command lines directly:
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
*(Note: `OS_INSECURE="true"` is mandatory because the academic cloud uses a self-signed SSL certificate).*

#### 🔑 macOS / Linux (Terminal):
Export the values like this:
```bash
export OS_AUTH_URL="https://private-cloud.informatik.hs-fulda.de:5000/v3"
export OS_USERNAME="CloudComp13"
export OS_PASSWORD="Hulk@3000"
export OS_PROJECT_NAME="CloudComp13"
export OS_USER_DOMAIN_NAME="Default"
export OS_PROJECT_DOMAIN_NAME="Default"
export OS_IDENTITY_API_VERSION="3"
export OS_INSECURE="true"
```

---

## Phase 4: Local Pulumi Setup & Stack Configuration

Instead of uploading infrastructure logs/state to Pulumi's cloud server, we configure the CLI to store state locally on the hard drive.

### 1. Log into Local State Engine
```bash
pulumi login --local
```
*   *What this does*: Creates a local workspace metadata folder inside `~/.pulumi` to save configuration state.

### 2. Prepare the Python Virtual Environment
Navigate to the `infra/` folder and setup dependencies:
```bash
# Navigate to the infra directory
cd infra

# Create a virtual environment
python -m venv venv

# Activate virtual environment (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Activate virtual environment (macOS/Linux)
# source venv/bin/activate

# Upgrade pip and install libraries (e.g., pulumi-openstack)
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Initialize Stack Configuration Passphrase
Since we store stack variables locally, we set a passphrase to encrypt secret configurations (like the DB password) inside the stack file:

#### Windows (PowerShell):
```powershell
$env:PULUMI_CONFIG_PASSPHRASE="Fulda2025"
```
#### macOS / Linux (Terminal):
```bash
export PULUMI_CONFIG_PASSPHRASE="Fulda2025"
```

### 4. Initialize and Configure the Stack
Create or select the `dev` environment stack and define configurations:
```bash
# Initialize stack if doing it for the first time
pulumi stack init dev

# Select it
pulumi stack select dev

# Set configuration variables
pulumi config set db_username fulda_user
pulumi config set db_name fulda_app
pulumi config set --secret db_password "Hulk@3000"
pulumi config set key_name fulda-key-new
pulumi config set instance_count 1
```

*   **`--secret db_password`**: Tells Pulumi to encrypt the password `"Hulk@3000"` using the `PULUMI_CONFIG_PASSPHRASE`. If you open the generated `Pulumi.dev.yaml` file, you will notice the password is represented as a secure ciphertext block, making it safe for git commits.

---

## Phase 5: Deploying Cloud Infrastructure (IaC)

Now, we execute the Python blueprint which defines our network, subnets, routers, security firewalls, Swift container, database instance, and web server instance.

### 1. Preview changes (Dry Run)
Verify everything builds without error:
```bash
pulumi preview
```
This contacts the OpenStack endpoints, runs dry-run API calls, and prints a chart showing what will be created.

### 2. Deploy Infrastructure
Execute the provision commands:
```bash
pulumi up
```
*   **Confirmation**: Select `yes` using arrow keys and press Enter.
*   **Bootstrapper execution**: Pulumi will create the resources. It takes roughly 3-5 minutes for OpenStack to assign storage, initialize networks, and boot the Ubuntu VMs.

### 3. Save the Outputs
At the end of a successful run, Pulumi prints the outputs. Note these:
*   `Web_Primary_Public_IP` (e.g. `10.32.6.178`)
*   `DB_Private_IP` (e.g. `10.0.1.123`)
*   `Swift_Container_Name` (e.g. `fulda-assets`)

---

## Phase 6: SSH Connecting & Deploying the Application Stack

Once the virtual hardware is created by Pulumi, we must log into the web server VM, download our code, and run it.

### 1. SSH into the Web VM
Run this command from your local machine (within the `infra/` folder containing the private key):
```bash
ssh -i fulda-key-new.pem ubuntu@<Web_Primary_Public_IP>
```
*(Replace `<Web_Primary_Public_IP>` with the actual IP address output by Pulumi, such as `10.32.6.178`).*

*   **Bootstrapping verification**: The VM automatically runs a boot-script that installs Git, Docker, and Docker Compose. You can verify they are ready on the VM terminal by typing:
    ```bash
    docker --version && docker-compose --version
    ```

### 2. Clone the Codebase
Once logged into the server, download the project files:
```bash
git clone https://github.com/darshanpeddadad/CloudComputing-13.git app
cd app
```

### 3. Create the Production Environment Settings
We must create a `.env` configuration file in the `Backend/` directory. Nginx and FastAPI read these settings.

Create the file:
```bash
nano Backend/.env
```

Paste the following variables into the file, replacing `<DB_Private_IP_from_pulumi_output>` with your DB IP (e.g., `10.0.1.123`):

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

> [!IMPORTANT]
> **Database Password URL Encoding**: The database password contains the `@` character (`Hulk@3000`). Because connection strings format URLs as `user:password@host`, database driver libraries split connection configurations at the `@` symbol. 
> 
> Therefore, you **MUST** URL-encode the `@` character as **`%40`** in the `DATABASE_URL` string: `Hulk%403000`. Failing to do so causes a driver database crash during start.

### 4. Build and Launch the Application Containers
Run the Docker Compose suite from the project root:
```bash
sudo docker-compose up --build -d
```
*   **What this does**:
    1.  Downloads the official Python & Nginx runtimes.
    2.  Compiles the React frontend codebase into static production assets inside the multi-stage Nginx build environment.
    3.  Spins up the FastAPI backend web server container on port 8000.
    4.  Hosts the Nginx reverse-proxy on host port 80, routing API calls to the backend and serving frontend files to incoming requests.

---

## Phase 7: Database Seeding & Migration

With the containers running, we must create the database tables and seed initial sample data.

Execute these commands from your Web VM's terminal inside the `app/` folder:

### 1. Database Table Creation (Alembic Migration)
```bash
sudo docker exec fastapi-backend alembic upgrade head
```
*   *What this does*: Instructs the backend container to execute SQLAlchemy Alembic migration scripts, generating table relations on the private MySQL VM.

### 2. Seeding Event Data
```bash
sudo docker exec -e PYTHONPATH=/app fastapi-backend python scripts/seed_events.py
```
*   *What this does*: Populates categories and event lists into the MySQL database.

---

## Phase 8: Accessing and Verifying the Deployment

Since the OpenStack instances are deployed inside the private University network infrastructure:

1.  Ensure you are connected to the **University Campus Wi-Fi** or logged into the **University VPN**.
2.  Open your web browser and test the following URLs (replacing `10.32.6.178` with your actual public Floating IP):

*   **Frontend Dashboard**: `http://10.32.6.178`
*   **Swagger API Docs**: `http://10.32.6.178/api/docs`
*   **API Health Status**: `http://10.32.6.178/api/health`
    *   This queries the private database server from the backend. A healthy connection returns:
        ```json
        {"status":"healthy"}
        ```

---

## Phase 9: Tearing Down Infrastructure

To destroy the servers and stop consuming resources on the OpenStack cloud:

1.  Navigate to your local computer's `infra/` folder.
2.  Run the tear down commands:
    ```bash
    pulumi destroy
    ```
3.  Type `yes` when prompted. Pulumi will safely delete the instances, routers, network interfaces, subnets, and Swift containers in the correct order.
4.  *(Optional)* To remove the local stack metadata configuration completely:
    ```bash
    pulumi stack rm dev
    ```
