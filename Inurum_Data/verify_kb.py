#!/usr/bin/env python3
import os
import re

BASE_DIR = "/Users/shubhamjain/Documents/pai/ModelPreTrain/inurum_kb/company_knowledge_base"

expected_dirs = {
    "company": 3,          # company_overview, leadership_team, partnerships_awards
    "policies": 10,        # 10 policies
    "employees": 54,       # 54 employees
    "departments": 10,     # 10 departments
    "projects": 27,        # 27 projects
    "services": 10,        # 10 services
    "clients": 32,         # 32 clients
    "products": 3,         # 3 products
    "sops": 8,             # 8 SOPs
    "technical_docs": 7,   # 7 technical docs
    "meetings": 5,         # 5 meetings
    "training": 5,         # 5 training manuals
    "contracts": 5,        # 5 contracts
    "faq": 12,             # 12 FAQ groups
    "glossary": 1          # 1 glossary file
}

errors = []
successes = []

print("Starting validation of Inurum Company Knowledge Base...\n")

# 1. Check folder presence and file counts
for folder, min_count in expected_dirs.items():
    path = os.path.join(BASE_DIR, folder)
    if not os.path.exists(path):
        errors.append(f"Directory missing: {folder}")
        continue
    
    files = [f for f in os.listdir(path) if f.endswith(".md")]
    count = len(files)
    if count < min_count:
        errors.append(f"Directory {folder} contains {count} files, expected at least {min_count}")
    else:
        successes.append(f"Directory {folder} contains {count} files (Passed minimum {min_count})")

# 2. Check metadata block and headings in all files
required_frontmatter = [
    "document_id:",
    "document_type:",
    "department:",
    "owner:",
    "created_date:",
    "last_updated:",
    "version:",
    "confidentiality:",
    "tags:",
    "keywords:",
    "aliases:",
    "related_documents:"
]

required_headings = [
    r"^# ",
    r"^## Overview",
    r"^## Detailed Information",
    r"^## Related Information",
    r"^## FAQ",
    r"^## Keywords"
]

total_checked = 0
total_faqs = 0

for root, dirs, files in os.walk(BASE_DIR):
    for file in files:
        if not file.endswith(".md"):
            continue
        total_checked += 1
        filepath = os.path.join(root, file)
        
        with open(filepath, "r") as f:
            content = f.read()
            
        # Check frontmatter bounds
        if not content.startswith("---\n"):
            errors.append(f"{file} does not start with standard '---'")
            continue
            
        fm_end_match = re.search(r"------------------\n", content)
        if not fm_end_match:
            errors.append(f"{file} is missing closing frontmatter dashed line ('------------------')")
            continue
            
        frontmatter = content[:fm_end_match.start()]
        
        # Check all required keys in frontmatter
        for key in required_frontmatter:
            if key not in frontmatter:
                errors.append(f"{file} frontmatter is missing key: {key}")
                
        # Check headings
        for pattern in required_headings:
            if not re.search(pattern, content, re.MULTILINE):
                errors.append(f"{file} is missing heading matching: {pattern}")
                
        # Check for placeholders
        if "Lorem Ipsum" in content or "Lorem ipsum" in content or "placeholder" in content.lower():
            errors.append(f"{file} contains placeholder text.")
            
        # Check word counts
        words = content.split()
        word_count = len(words)
        if word_count > 900:
            errors.append(f"{file} is too long ({word_count} words). Recommended limit is 500-800 words.")
        elif word_count < 100:
            errors.append(f"{file} is too short ({word_count} words).")
            
        # Count Q&A sections in FAQs
        if "faq" in root:
            # We count instances of Q01, Q02, etc. or "### Q" in the file
            q_matches = re.findall(r"### Q\d+:", content)
            total_faqs += len(q_matches)

print(f"Total checked files: {total_checked}")
print(f"Total FAQs found across FAQ files: {total_faqs}")

if total_faqs < 300:
    errors.append(f"Total FAQs found is {total_faqs}, expected at least 300 unique Q&As")
else:
    successes.append(f"Total FAQs verified: {total_faqs} (Passed minimum 300)")

if errors:
    print("\n--- VALIDATION ERRORS FOUND ---")
    for err in errors[:30]:  # Limit printout length
        print(f"[ERROR] {err}")
    if len(errors) > 30:
        print(f"...and {len(errors) - 30} more errors.")
else:
    print("\n--- ALL VALIDATIONS PASSED SUCCESSFULLY ---")
    for suc in successes:
        print(f"[OK] {suc}")
