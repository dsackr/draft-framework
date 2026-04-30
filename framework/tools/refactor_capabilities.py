import os
import yaml
from pathlib import Path

def refactor_file(file_path):
    with open(file_path, 'r') as f:
        try:
            data = yaml.safe_load(f)
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            return False

    if not isinstance(data, dict):
        return False

    changed = False

    # 1. Base object migration
    if 'addressesConcerns' in data:
        data['capabilities'] = data.pop('addressesConcerns')
        changed = True

    if 'capability' in data:
        new_caps = data.pop('capability')
        if isinstance(new_caps, str):
            new_caps = [new_caps]

        existing_caps = data.get('capabilities', [])
        if not isinstance(existing_caps, list):
            existing_caps = [existing_caps]

        data['capabilities'] = list(set(existing_caps + new_caps))
        changed = True

    # 2. Configurations migration for Technology Components
    if 'configurations' in data and isinstance(data['configurations'], list):
        for config in data['configurations']:
            if 'addressesConcerns' in config:
                config['capabilities'] = config.pop('addressesConcerns')
                changed = True

    # 3. External interactions migration for Standards, Software Deployment
    # Patterns, and Reference Architectures
    def refactor_interactions(interactions):
        nonlocal changed
        if not isinstance(interactions, list):
            return
        for inter in interactions:
            if 'capability' in inter:
                inter['capabilities'] = [inter.pop('capability')]
                changed = True

    if 'externalInteractions' in data:
        refactor_interactions(data['externalInteractions'])

    # 4. Service groups for Software Deployment Patterns and Reference Architectures
    if 'serviceGroups' in data and isinstance(data['serviceGroups'], list):
        for group in data['serviceGroups']:
            if 'externalInteractions' in group:
                refactor_interactions(group['externalInteractions'])

    if changed:
        with open(file_path, 'w') as f:
            yaml.dump(data, f, sort_keys=False)
        return True
    return False

def main():
    repo_root = Path(__file__).resolve().parents[2]
    folders = [
        "examples/catalog/technology-components",
        "examples/catalog/appliance-components",
        "examples/catalog/host-standards",
        "examples/catalog/service-standards",
        "examples/catalog/database-standards",
        "examples/catalog/software-deployment-patterns",
        "examples/catalog/decision-records",
        "examples/catalog/product-services",
        "examples/catalog/saas-services",
        "examples/catalog/paas-services",
        "examples/catalog/reference-architectures",
        "framework/configurations/definition-checklists",
    ]
    count = 0
    for folder in folders:
        path = repo_root / folder
        if not path.exists():
            continue
        for file in path.rglob("*.yaml"):
            if refactor_file(file):
                print(f"Refactored {file}")
                count += 1
    print(f"Total files refactored: {count}")

if __name__ == "__main__":
    main()
