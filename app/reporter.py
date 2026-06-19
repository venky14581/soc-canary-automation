import json
import csv
import os
import logging
import http.client
from urllib.parse import urlparse
from logging.handlers import RotatingFileHandler
from app.database import DatabaseManager

def setup_logger(name, log_file, level=logging.INFO):
    handler = RotatingFileHandler(log_file, maxBytes=10485760, backupCount=5)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if not logger.handlers:
        logger.addHandler(handler)
    return logger

soc_log = setup_logger("soc_reporting", "soc_reporting.log")

class SOCReporter:
    def __init__(self):
        self.db = DatabaseManager()

    def send_to_soc_server(self, soc_url, payload):
        """Transmits JSON telemetry records to an enterprise SOC endpoint."""
        if not soc_url:
            return
        
        soc_log.info(f"Forwarding log bundles to SOC server at: {soc_url}")
        try:
            parsed_url = urlparse(soc_url)
            port = parsed_url.port if parsed_url.port else (443 if parsed_url.scheme == "https" else 80)
            
            if parsed_url.scheme == "https":
                import ssl
                conn = http.client.HTTPSConnection(parsed_url.hostname, port, context=ssl._create_unverified_context())
            else:
                conn = http.client.HTTPConnection(parsed_url.hostname, port)

            headers = {'Content-Type': 'application/json'}
            conn.request("POST", parsed_url.path if parsed_url.path else "/", json.dumps(payload), headers)
            response = conn.getresponse()
            
            if response.status in [200, 201, 202]:
                soc_log.info(f"SIEM Ingestion Success: Status {response.status}")
            else:
                soc_log.error(f"SIEM Ingestion Rejected: Status {response.status} - {response.read().decode()}")
            conn.close()
        except Exception as e:
            soc_log.error(f"Network transport error during SOC collection: {str(e)}")

    def generate_consolidated_reports(self, soc_url=None):
        soc_log.info("Generating aggregated system posture reports.")
        try:
            with self.db._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT d.hostname, d.ip_address, d.file_name, d.deployment_path, v.status, d.timestamp
                    FROM deployments d
                    LEFT JOIN validation_results v ON d.id = v.deployment_id
                """)
                records = cursor.fetchall()

            headers = ["Hostname", "IP Address", "File Name", "Deployment Path", "Validation Result", "Timestamp"]
            
            json_payload = []
            for item in records:
                json_payload.append({
                    "hostname": item[0],
                    "ip": item[1],
                    "file": item[2],
                    "path": item[3],
                    "status": item[4] if item[4] else "Unknown",
                    "timestamp": item[5]
                })

            # Save Locally
            with open("Deployment_Report.json", "w", encoding="utf-8") as f:
                json.dump(json_payload, f, indent=4)

            with open("Deployment_Report.csv", "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                writer.writerows(records)

            # Transmit Remotely
            if soc_url and json_payload:
                self.send_to_soc_server(soc_url, json_payload)

            return True
        except Exception as e:
            soc_log.error(f"Failed to generate enterprise reports: {str(e)}")
            return False