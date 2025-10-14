"""Test script to verify all MCP tools work correctly."""

from technology_detector import detect_technology
from checklist_engine import ChecklistEngine
from pathlib import Path
import json

print("=" * 60)
print("Testing MCP Code Reviewer Tools")
print("=" * 60)

# Test 1: detect_technology
print("\n1. Testing detect_technology...")
try:
    result = detect_technology(".")
    print(f"✅ Success: {json.dumps(result, indent=2)}")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 2: ChecklistEngine - get_available_checklists
print("\n2. Testing get_available_checklists...")
try:
    engine = ChecklistEngine(".")
    checklists = engine.get_available_checklists()
    print(f"✅ Success: Found {len(checklists)} checklists")
    print(f"   Available: {checklists}")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 3: ChecklistEngine - load_checklist
print("\n3. Testing load_checklist (python)...")
try:
    engine = ChecklistEngine(".")
    checklist = engine.load_checklist("python")
    print(f"✅ Success: Loaded checklist for {checklist['technology']}")
    print(f"   Categories: {len(checklist['categories'])}")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 4: Review code (this might take longer)
print("\n4. Testing review_code...")
try:
    engine = ChecklistEngine(".")

    def progress_callback(progress):
        status = "in progress" if progress['in_progress'] else "waiting"
        print(f"   Progress: {progress['percentage']:.1f}% - {status}")

    summary = engine.review_code("python", progress_callback=progress_callback)
    print(f"✅ Success: Review completed")
    print(f"   Total: {summary['total']}, Passed: {summary['passed']}, Failed: {summary['failed']}, Skipped: {summary['skipped']}")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 60)
print("Testing Complete!")
print("=" * 60)
