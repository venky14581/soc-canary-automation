import os
import shutil
import hashlib
import logging
import json  # Added for structuring SOC JSON events
import datetime  # Added for accurate UTC logging
from logging.handlers import RotatingFileHandler
import win32wnet
import win32netcon  
from app.database import DatabaseManager

def setup_logger(name, log_file, level=logging.INFO):
    handler = RotatingFileHandler(log_file, maxBytes=5242880, backupCount=2)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if not logger.handlers:
        logger.addHandler(handler)
    return logger

deploy_log = setup_logger("deployment", "deployment.log")
valid_log = setup_logger("validation", "validation.log")

class DeploymentEngine:
    def __init__(self):
        self.db = DatabaseManager()
        # Ensure the custom telemetry logs directory exists for NXLog to capture
        self.soc_log_dir = "C:\\canary_logs"
        os.makedirs(self.soc_log_dir, exist_ok=True)
        self.soc_log_file = os.path.join(self.soc_log_dir, "deployments.json")

    def emit_soc_telemetry(self, hostname, ip, file_name, method, status, dest_path, error_msg=""):
        """Generates a structured JSON line entry that NXLog can parse instantly."""
        payload = {
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "integration": "canary_deployer",
            "target_host": str(hostname),
            "target_ip": str(ip),
            "deployment_method": str(method),
            "file_deployed": str(file_name),
            "status": str(status),
            "destination_path": str(dest_path),
            "error_details": str(error_msg)
        }
        try:
            with open(self.soc_log_file, "a") as f:
                f.write(json.dumps(payload) + "\n")
        except Exception as e:
            deploy_log.error(f"Failed to write NXLog pipeline telemetry: {str(e)}")

    @staticmethod
    def calculate_hash(file_path):
        hasher = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                buf = f.read(65536)
                while len(buf) > 0:
                    hasher.update(buf)
                    buf = f.read(65536)
            return hasher.hexdigest()
        except Exception:
            return ""

    def establish_smb_connection(self, remote_unc, username, password):
        if not username or not password:
            return True  
        try:
            nr = win32wnet.NETRESOURCE()
            nr.dwType = win32netcon.RESOURCETYPE_DISK
            nr.lpRemoteName = remote_unc
            win32wnet.WNetAddConnection2(nr, password, username, 0)
            return True
        except Exception as e:
            deploy_log.error(f"Network IPC connection rejected for {remote_unc}: {str(e)}")
            return False

    def remove_smb_connection(self, remote_unc):
        try:
            win32wnet.WNetCancelConnection2(remote_unc, 0, int(True))
        except Exception:
            pass

    def deploy_to_endpoint(self, host_info, source_file, target_path, username=None, password=None):
        hostname = host_info['Hostname']
        ip = host_info['IP Address']
        method = host_info.get('Deployment Method', 'SMB')
        file_name = os.path.basename(source_file)

        is_local = str(hostname).lower() in ["localhost", "127.0.0.1"] or str(method).lower() == "local"
        deploy_log.info(f"Targeting Node -> Host: {hostname} (Local={is_local}), File: {file_name}")

        if is_local:
            dest_full_path = os.path.join(target_path, file_name)
        else:
            drive, path_tail = os.path.splitdrive(target_path)
            share_letter = drive.replace(":", "$") if drive else "C$"
            clean_tail = path_tail.lstrip("\\").lstrip("/")
            
            base_unc = f"\\\\{ip}\\{share_letter}"
            dest_full_path = os.path.join(base_unc, clean_tail, file_name)
            
            if not self.establish_smb_connection(base_unc, username, password):
                self.db.log_deployment(hostname, ip, file_name, target_path, method, "Auth Failed")
                # SOC Telemetry: Authentication failure alert routing
                self.emit_soc_telemetry(hostname, ip, file_name, method, "Failed", target_path, "Authentication denied over IPC.")
                return {"host": hostname, "status": "Failed", "msg": "Authentication denied over IPC."}

        try:
            os.makedirs(os.path.dirname(dest_full_path), exist_ok=True)
            shutil.copy2(source_file, dest_full_path)
            
            dep_id = self.db.log_deployment(hostname, ip, file_name, dest_full_path, method, "Success")
            val_status = self.validate_deployment(source_file, dest_full_path, dep_id)
            
            if not is_local:
                self.remove_smb_connection(base_unc)
            
            # SOC Telemetry: Successful deployment entry
            self.emit_soc_telemetry(hostname, ip, file_name, method, val_status, dest_full_path)
            return {"host": hostname, "status": val_status, "path": dest_full_path}

        except Exception as e:
            deploy_log.error(f"Write operation failed on target host {hostname}: {str(e)}")
            self.db.log_deployment(hostname, ip, file_name, target_path, method, f"Error: {str(e)}")
            if not is_local:
                self.remove_smb_connection(base_unc)
            
            # SOC Telemetry: System execution failure writeout
            self.emit_soc_telemetry(hostname, ip, file_name, method, "Failed", target_path, str(e))
            return {"host": hostname, "status": "Failed", "msg": str(e)}

    def validate_deployment(self, source_path, dest_path, deployment_id):
        try:
            exists = os.path.exists(dest_path)
            size_match = False
            hash_match = False

            if exists:
                size_match = os.path.getsize(source_path) == os.path.getsize(dest_path)
                hash_match = self.calculate_hash(source_path) == self.calculate_hash(dest_path)

            status = "Success" if (exists and size_match and hash_match) else "Partial Success"
            if not exists:
                status = "Failed"

            self.db.log_validation(deployment_id, exists, size_match, hash_match, status)
            return status
        except Exception as e:
            valid_log.error(f"Validation failure for ID {deployment_id}: {str(e)}")
            self.db.log_validation(deployment_id, False, False, False, f"Error: {str(e)}")
            return "Failed"