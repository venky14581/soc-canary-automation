\# Autonomous Canary Deployment \& SIEM Telemetry Framework



\## Overview



The \*\*Autonomous Canary Deployment \& SIEM Telemetry Framework\*\* is an enterprise-grade security orchestration solution designed to automate the deployment, verification, tracking, and reporting of canary files (honeytokens) across distributed Windows environments.



The framework provides:



\* Centralized graphical deployment management

\* Remote endpoint file deployment

\* Integrity verification using cryptographic hashes

\* SQLite-based deployment tracking

\* Automated JSON and CSV reporting

\* Real-time telemetry generation

\* Integration with enterprise SIEM platforms such as Wazuh via NXLog



\---



\# Key Features



\### Remote Canary Deployment



Deploy canary documents to remote Windows systems using authenticated SMB communication.



\### Integrity Validation



Automatically compute and verify file hashes to ensure successful deployment.



\### Local Deployment Database



Maintain complete deployment history using SQLite.



\### Automated Reporting



Generate machine-readable and analyst-friendly reports:



\* Deployment\_Report.json

\* Deployment\_Report.csv



\### Real-Time Telemetry Streaming



Produce structured JSON telemetry events suitable for:



\* Wazuh

\* Splunk

\* Elastic SIEM

\* QRadar

\* Sentinel



\### Centralized GUI



Operate deployments through a user-friendly graphical console without requiring command-line interaction.



\---



\# Architecture



```text

+-----------------------------+

|      Management Console     |

|          (GUI)              |

+-------------+---------------+

&#x20;             |

&#x20;             v

+-----------------------------+

|    Deployment Orchestrator  |

|        (engine.py)          |

+-------------+---------------+

&#x20;             |

&#x20;     SMB / IPC Authentication

&#x20;             |

&#x20;             v

+-----------------------------+

|      Windows Endpoint       |

|     Canary File Storage     |

+-------------+---------------+

&#x20;             |

&#x20;             v

+-----------------------------+

| Structured JSON Log Writer  |

+-------------+---------------+

&#x20;             |

&#x20;             v

+-----------------------------+

|           NXLog             |

|      Log Forwarder          |

+-------------+---------------+

&#x20;             |

&#x20;     UDP Syslog Transport

&#x20;             |

&#x20;             v

+-----------------------------+

|         Wazuh SIEM          |

|         SOC Console         |

+-----------------------------+

```



\---



\# Repository Structure



```text

Canary\_Deployer/

│

├── app/

│   ├── \_\_init\_\_.py

│   ├── database.py

│   ├── engine.py

│   └── reporter.py

│

├── main.py

├── mock\_soc.py

├── requirements.txt

├── README.md

└── .gitignore

```



\---



\# Component Description



\## database.py



Responsible for:



\* SQLite database initialization

\* Deployment record insertion

\* Querying historical deployments

\* Audit tracking



\---



\## engine.py



Responsible for:



\* SMB authentication

\* Remote file transfer

\* Hash generation

\* Integrity verification

\* Deployment status handling



\---



\## reporter.py



Responsible for:



\* JSON report generation

\* CSV report generation

\* Deployment statistics aggregation

\* Telemetry formatting



\---



\## main.py



Application entry point providing:



\* Graphical User Interface

\* Deployment execution controls

\* Target management

\* Reporting dashboard



\---



\## mock\_soc.py



Lightweight testing server that:



\* Receives telemetry events

\* Displays formatted deployment logs

\* Simulates SOC ingestion workflows



\---



\# Installation



\## Step 1: Clone Repository



```powershell

git clone <repository-url>



cd Canary\_Deployer

```



\---



\## Step 2: Create Virtual Environment



```powershell

python -m venv venv

```



\---



\## Step 3: Activate Environment



```powershell

.\\venv\\Scripts\\activate

```



\---



\## Step 4: Install Dependencies



```powershell

pip install -r requirements.txt

```



\---



\# Target Endpoint Preparation



\## Virtual Machine Targets



Run the following commands as Administrator:



```powershell

Set-NetConnectionProfile -NetworkCategory Private



Set-NetFirewallRule -DisplayGroup "Network Discovery" -Enabled True



Set-NetFirewallRule -DisplayGroup "Remote Service Management" -Enabled True

```



Ensure:



\* Password authentication is enabled

\* A local account password is configured

\* SMB connectivity is available



\---



\## Physical Machine Targets



Run as Administrator:



```powershell

New-ItemProperty `

\-Path "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" `

\-Name "LocalAccountTokenFilterPolicy" `

\-Value 1 `

\-PropertyType DWord `

\-Force

```



Enable required firewall rules:



```powershell

Set-NetConnectionProfile -NetworkCategory Private



Set-NetFirewallRule -DisplayGroup "File and Printer Sharing" -Enabled True



Set-NetFirewallRule -DisplayGroup "Remote Service Management" -Enabled True

```



\---



\# Credential Models



\## Administrator Credentials



Supports deployment to administrative shares:



```text

\\\\HOST\\C$

\\\\HOST\\D$

```



Example:



```text

C:\\CanaryTest

C:\\Users\\Public\\Documents

```



\---



\## Standard User Credentials



Requires a manually shared folder:



Example:



```text

\\\\HOST\\CanaryShare

```



The user must be granted:



\* Read Permission

\* Write Permission



\---



\# Running the Framework



Start the GUI:



```powershell

python main.py

```



\---



\# Testing Mode



\## Mock SOC Mode



Start telemetry receiver:



```powershell

python mock\_soc.py

```



Default listener:



```text

http://localhost:8080

```



All deployment telemetry will be displayed in real time.



\---



\# Enterprise SIEM Integration



\## NXLog Configuration



Monitor:



```text

C:\\canary\_logs\\deployments.json

```



Forward logs to:



```text

UDP 514

```



\---



\## Wazuh Configuration



Configure Wazuh Manager to receive remote syslog events.



Typical configuration file:



```text

/var/ossec/etc/ossec.conf

```



\---



\# Generated Reports



After deployment, the framework generates:



```text

database.db



Deployment\_Report.json



Deployment\_Report.csv

```



\---



\# Sample Telemetry Event



```json

{

&#x20; "timestamp": "2026-06-19T12:54:10Z",

&#x20; "integration": "canary\_deployer",

&#x20; "target\_host": "VirtualBox-Win11",

&#x20; "target\_ip": "192.168.10.38",

&#x20; "file\_deployed": "AdmitCard-26041083.pdf",

&#x20; "destination\_path": "\\\\\\\\192.168.10.38\\\\C$\\\\CanaryTest\\\\",

&#x20; "status": "Success"

}

```



\---



\# Verification Checklist



\### Deployment Validation



\* \[ ] File exists on target endpoint

\* \[ ] Hash verification passed

\* \[ ] Deployment recorded in SQLite database



\### Reporting Validation



\* \[ ] JSON report generated

\* \[ ] CSV report generated



\### Telemetry Validation



\* \[ ] Telemetry event generated

\* \[ ] Event forwarded via NXLog

\* \[ ] Event visible in SIEM dashboard



\---



\# Security Considerations



\* Store credentials securely.

\* Restrict administrative share access.

\* Encrypt telemetry channels where required.

\* Periodically rotate deployment accounts.

\* Limit deployment scope using organizational policies.



\---



\# Future Enhancements



\* Multi-host deployment scheduling

\* Canary file lifecycle management

\* Active Directory integration

\* Role-based access control (RBAC)

\* PowerShell Remoting support

\* Secure TLS telemetry transport

\* Centralized deployment dashboard

\* Automated canary rotation



\---



\# License



This project is intended for authorized security testing, deception engineering, validation exercises, and defensive security operations within approved environments.



