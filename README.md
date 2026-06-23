# Autonomous Canary Deployment & SIEM Telemetry Framework

## Academic Evaluation and Demonstration Manual

> **Authorized use only:** Use this framework only on systems, virtual machines, and lab networks where you have explicit authorization.

---

## 1. Project Overview

The **Autonomous Canary Deployment & SIEM Telemetry Framework** is a defensive security orchestration project used to deploy harmless canary files (honeytokens) to authorized Windows endpoints.

The framework supports:

- Centralized graphical deployment management
- Local and remote Windows endpoint deployment
- Authenticated SMB-based file transfer
- Cryptographic hash generation and integrity verification
- SQLite-based deployment history tracking
- Automatic JSON and CSV report generation
- Real-time telemetry generation
- Mock SOC testing mode
- Enterprise SIEM integration through NXLog and Wazuh

---

## 2. Repository Structure

```text
Canary_Deployer/
│
├── app/
│   ├── __init__.py
│   ├── database.py
│   ├── engine.py
│   └── reporter.py
│
├── main.py
├── mock_soc.py
├── requirements.txt
├── README.md
└── .gitignore
```

### Component Responsibilities

| File | Responsibility |
|---|---|
| `main.py` | Starts the graphical user interface and deployment controls |
| `app/engine.py` | Handles deployment orchestration, SMB transfer, hashing, and validation |
| `app/database.py` | Stores deployment history and audit records in SQLite |
| `app/reporter.py` | Creates JSON, CSV, and telemetry output |
| `mock_soc.py` | Receives and displays real-time SOC telemetry events |

---

## 3. Phase 1: Host Environment Setup

### Step 1: Extract the Project Archive

Extract the project ZIP file to a suitable location.

Example:

```text
D:\Canary_Deployer
```

Open PowerShell inside the extracted project directory.

### Step 2: Verify Python Version

The project should preferably use Python 3.12.x.

```powershell
python --version
```

### Step 3: Create a Virtual Environment

```powershell
python -m venv venv
```

### Step 4: Activate the Virtual Environment

```powershell
.\venv\Scripts\activate
```

### Step 5: Install Dependencies

```powershell
pip install -r requirements.txt
```

---

## 4. Phase 2: Target Endpoint Preparation

The target endpoint can be:

- A Windows Virtual Machine in VirtualBox
- A physical Windows computer in an authorized lab network
- The same local computer for local deployment testing

### Step 1: Find the Target Username

On the target Windows system:

```powershell
[System.Security.Principal.WindowsIdentity]::GetCurrent().Name
```

Use the appropriate credential format:

| Account Type | Username Format |
|---|---|
| Local account | `.\username` |
| Domain account | `DOMAIN\username` |
| School or Microsoft account | `username@school.com` |

### Step 2: Find the Target IP Address

On the target system:

```powershell
ipconfig
```

Find the IPv4 address and use it in the GUI endpoint inventory.

### Step 3: Configure Network Profile

Open PowerShell as Administrator on the target machine:

```powershell
Set-NetConnectionProfile -NetworkCategory Private
```

### Step 4: Enable Required Firewall Rules

Run as Administrator:

```powershell
Set-NetFirewallRule -DisplayGroup "File and Printer Sharing" -Enabled True
Set-NetFirewallRule -DisplayGroup "Network Discovery" -Enabled True
Set-NetFirewallRule -DisplayGroup "Remote Service Management" -Enabled True
```

### Step 5: Configure Password Authentication

For SMB deployment:

- The target account must have a proper password.
- Do not use a blank password.
- Windows Hello PIN-only authentication may not work for SMB deployment.
- Use a normal local or domain account password.

---

## 5. Deployment Credential Models

### Model A: Administrator Credentials

Administrator credentials can deploy files through Windows administrative shares.

```text
\\HOST\C$
\\HOST\D$
```

Example destination paths:

```text
C:\CanaryTest
C:\Users\Public\Documents
C:\Users\Public\CanaryTest\Documents
```

For remote administrative-share deployment in an authorized lab environment, run the following as Administrator on the target machine:

```powershell
New-ItemProperty `
-Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" `
-Name "LocalAccountTokenFilterPolicy" `
-Value 1 `
-PropertyType DWord `
-Force
```

### Model B: Standard User Credentials

If using a non-administrator account, create and share a dedicated folder such as:

```text
C:\CanaryShare
```

Share it as:

```text
\\HOST\CanaryShare
```

Ensure the selected user has:

- Read permission
- Write permission
- Network access permission

Use this model for safer academic demonstrations when administrative shares are not required.

---

## 6. Phase 3: Mock SOC Telemetry Setup

For standalone demonstration without Wazuh or another SIEM platform, start the included Mock SOC receiver.

Open a new PowerShell terminal inside the project folder:

```powershell
.\venv\Scripts\activate
python mock_soc.py
```

The receiver listens on:

```text
http://localhost:8080
```

Use the following ingestion URL in the GUI:

```text
http://127.0.0.1:8080/api/logs
```

The Mock SOC terminal should display deployment telemetry events in real time.

---

## 7. Phase 4: Enterprise SIEM Integration

### NXLog

Configure NXLog to monitor:

```text
C:\canary_logs\deployments.json
```

NXLog should forward structured deployment events to the SIEM collector.

### Wazuh

Configure the Wazuh Manager to receive remote syslog events.

Typical configuration file:

```text
/var/ossec/etc/ossec.conf
```

The Wazuh Manager should have an active syslog listener, commonly configured for:

```text
UDP Port 514
```

---

## 8. Phase 5: Start the GUI Application

From the main project directory:

```powershell
.\venv\Scripts\activate
python main.py
```

The GUI provides:

- Source file selection
- Endpoint inventory loading
- Target directory pattern selection
- Credential input
- SOC ingestion URL configuration
- Deployment execution controls
- Progress monitoring

---

## 9. GUI Input Fields

| GUI Field | Description | Example |
|---|---|---|
| Source Files | Harmless canary files to deploy | `Finance_Report.xlsx`, `Employee_List.docx` |
| Host/IP Address | Target endpoint IP address | `192.168.1.25` |
| User Principal | Authorized target account | `.\username` |
| Secret Key | Password for the authorized target account | Target account password |
| Target Directory | Folder where canary files will be placed | `C:\CanaryTest\Documents` |
| SOC Ingestion URL | Mock SOC endpoint | `http://127.0.0.1:8080/api/logs` |

Recommended harmless canary file types:

```text
.txt
.docx
.xlsx
.pdf
.csv
```

Do not deploy executable files or real sensitive data.

---

## 10. Deployment Execution Flow

1. Select source canary files.
2. Load or manually add endpoint inventory.
3. Select authorized target endpoints.
4. Select target directory patterns.
5. Enter authorized credentials.
6. Enter the SOC ingestion URL.
7. Click **Start Orchestrated Deployment Run**.

The framework will:

1. Authenticate to the target endpoint.
2. Transfer the selected canary files.
3. Generate cryptographic hashes.
4. Verify file integrity after deployment.
5. Store deployment information in SQLite.
6. Generate JSON and CSV reports.
7. Send telemetry to the SOC receiver.

---

## 11. Generated Output Files

After a successful deployment, the project should generate:

```text
database.db
Deployment_Report.json
Deployment_Report.csv
```

| File | Purpose |
|---|---|
| `database.db` | SQLite database containing deployment history and audit records |
| `Deployment_Report.json` | Structured machine-readable deployment report |
| `Deployment_Report.csv` | Spreadsheet-compatible deployment report |

---

## 12. Sample Telemetry Event

```json
{
  "timestamp": "2026-06-23T10:30:00Z",
  "integration": "canary_deployer",
  "target_host": "Windows-VM",
  "target_ip": "192.168.1.25",
  "file_deployed": "Finance_Report.xlsx",
  "destination_path": "\\\\192.168.1.25\\C$\\CanaryTest\\Documents\\Finance_Report.xlsx",
  "status": "Success"
}
```

---

## 13. Teacher Demonstration Checklist

### 1. Target Directory Proof

Open the target folder on the destination machine:

```text
C:\CanaryTest\Documents
```

Show that the canary files were successfully deployed.

### 2. Database and Reporting Proof

Open the project root directory and show:

```text
database.db
Deployment_Report.json
Deployment_Report.csv
```

Explain:

- `database.db` stores historical deployment records.
- `Deployment_Report.json` is used for structured automation and SOC integration.
- `Deployment_Report.csv` can be opened in Microsoft Excel for analysis.

### 3. SOC Telemetry Proof

Show the running terminal where you started:

```powershell
python mock_soc.py
```

Show that the telemetry event contains:

- Target hostname
- Target IP address
- File deployed
- Destination path
- Deployment status
- Hash validation result

---

## 14. Verification Checklist

### Deployment Validation

- [ ] File exists on the target endpoint.
- [ ] Hash verification passed.
- [ ] Deployment record exists in `database.db`.

### Reporting Validation

- [ ] `Deployment_Report.json` generated.
- [ ] `Deployment_Report.csv` generated.

### Telemetry Validation

- [ ] Telemetry event generated.
- [ ] Mock SOC received the event.
- [ ] Event includes target IP, deployed file, and destination path.

### Enterprise SIEM Validation

- [ ] NXLog monitors `C:\canary_logs\deployments.json`.
- [ ] NXLog forwards telemetry through UDP syslog.
- [ ] Wazuh receives the event.
- [ ] Event appears in the Wazuh dashboard.

---

## 15. Security Considerations

- Use only authorized endpoints and lab systems.
- Do not hardcode passwords in source code.
- Restrict administrative share access.
- Use a dedicated deployment account where possible.
- Use shared folders for standard-user demonstrations.
- Avoid using real confidential documents as canary files.
- Rotate deployment credentials periodically.
- Use encrypted telemetry transport in production environments.
- Limit deployment scope using organizational policies.

---

## 16. Future Enhancements

- Multi-host deployment scheduling
- Canary file lifecycle management
- Automatic canary rotation
- Active Directory integration
- Role-Based Access Control
- Secure TLS telemetry transport
- Centralized deployment dashboard
- PowerShell Remoting support

---

## License

This project is intended for authorized security testing, deception engineering, validation exercises, and defensive security operations within approved environments.
