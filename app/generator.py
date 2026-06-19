import os
import random
import string
from pathlib import Path

class SyntheticFileGenerator:
    @staticmethod
    def generate_random_string(length=500):
        letters = string.ascii_letters + string.digits + " \n\t"
        return ''.join(random.choice(letters) for _ in range(length))

    @staticmethod
    def create_synthetic_file(category, target_dir):
        os.makedirs(target_dir, exist_ok=True)
        
        pool = {
            "Finance": [("budget_2026.xlsx", "Financial Ledger Summary Data\n"), ("payroll_summary.xlsx", "ID,Name,Salary,Tax\n")],
            "Human Resources": [("employee_records.xlsx", "SSN,Name,Role,Address\n"), ("candidate_list.xlsx", "CV,Evaluation,Status\n")],
            "Business": [("strategy_plan.pdf", "%PDF-1.4 Corporate Strategy\n"), ("customer_database.xlsx", "UID,Email,Phone,LTV\n")],
            "Engineering": [("project_design.docx", "PK..Design Document Blueprint Metadata\n"), ("source_archive.zip", "PK..Archived Source Artifacts\n")],
            "Credentials Testing": [("saved_credentials.txt", "vault_key=enc(A89F..)\n"), ("browser_cookies_backup.txt", "session_id=z910f..\n")]
        }

        templates = pool.get(category, [("canary_file.txt", "Generic Canary Data\n")])
        selected = random.choice(templates)
        
        # Randomize filename to bypass fixed-name filters
        rand_prefix = ''.join(random.choice(string.ascii_lowercase) for _ in range(4))
        filename = f"{rand_prefix}_{selected[0]}"
        dest_path = os.path.join(target_dir, filename)

        content = selected[1] + SyntheticFileGenerator.generate_random_string(random.randint(200, 1000))
        
        with open(dest_path, "w", encoding="utf-8") as f:
            f.write(content)

        return dest_path