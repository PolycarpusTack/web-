#!/usr/bin/env python3
"""
Script to clean up duplicate virtual environments in the Web+ project.
Standardizes on using .venv in the project root.
"""

import os
import shutil
import sys
from pathlib import Path

def cleanup_venvs():
    """Clean up duplicate virtual environments."""
    project_root = Path(__file__).parent.parent
    
    # Virtual environments to remove (keeping only root .venv)
    venvs_to_remove = [
        project_root / "apps" / "backend" / "venv",
        project_root / "apps" / "backend" / ".venv"
    ]
    
    removed_count = 0
    
    for venv_path in venvs_to_remove:
        if venv_path.exists():
            print(f"Removing duplicate venv: {venv_path}")
            try:
                shutil.rmtree(venv_path)
                removed_count += 1
                print(f"  ✓ Removed successfully")
            except Exception as e:
                print(f"  ✗ Error removing {venv_path}: {e}")
    
    # Update scripts to use root .venv
    scripts_to_update = [
        project_root / "backend_sync.py",
        project_root / "start_web_plus.bat",
        project_root / "start_simple.py",
        project_root / "run_simple.py"
    ]
    
    for script_path in scripts_to_update:
        if script_path.exists():
            print(f"\nChecking script: {script_path.name}")
            try:
                with open(script_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Replace backend venv references with root venv
                original_content = content
                content = content.replace('apps/backend/venv', '.venv')
                content = content.replace('apps\\backend\\venv', '.venv')
                content = content.replace('apps/backend/.venv', '.venv')
                content = content.replace('apps\\backend\\.venv', '.venv')
                
                if content != original_content:
                    with open(script_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"  ✓ Updated venv references")
                else:
                    print(f"  - No changes needed")
                    
            except Exception as e:
                print(f"  ✗ Error updating {script_path}: {e}")
    
    print(f"\n✅ Cleanup complete! Removed {removed_count} duplicate venvs")
    print("\n📌 Standard virtual environment location: .venv (project root)")
    print("\n🔧 Next steps:")
    print("1. Ensure .venv exists in project root")
    print("2. Install dependencies: pip install -r requirements.txt")
    print("3. Run the application with updated scripts")

if __name__ == "__main__":
    cleanup_venvs()