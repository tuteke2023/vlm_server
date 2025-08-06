#!/usr/bin/env python3
"""
Cleanup script to remove duplicate and legacy files
Run with --dry-run first to see what would be deleted
"""

import os
import argparse
from pathlib import Path

# Files to remove from root directory (already exist in services/vlm/)
DUPLICATE_FILES = [
    "bank_parser.py",
    "bank_parser_v2.py", 
    "bank_parser_v3.py",
    "bank_statement_post_processor.py",
    "bank_table_parser_v3.py",
    "vlm_server.py",
    "transaction_classifier.py",
    "transaction_classifier_langchain.py",
    "vlm_langchain_endpoint.py",
]

# Test files that are no longer needed
OLD_TEST_FILES = [
    "test_bank_parser.py",
    "test_parser_v3.py",
    "test_parser_direct.py",
    "test_parser_issue.py",
    "test_langchain_integration.py",
    "test_increment1.py",
    "test_increment2.py", 
    "test_increment3.py",
    "test_increment4.py",
    "test_increment5.py",
    "vlm_server_increment1_patch.py",
]

# Old log files
OLD_LOG_FILES = [
    "server_langchain.log",
    "server_langchain_v2.log",
    "server_langchain_v3.log",
    "server_langchain_v3_fixed.log",
    "server_langchain_v4.log",
    "server_3b.log",
    "server_cpu.log",
    "server_cuda_fix.log",
    "server_env.log",
    "server_final.log",
    "server_fixed.log",
    "server_fixed_json.log",
    "server_fresh.log",
    "server_fresh2.log",
    "server_hf_official.log",
    "server_new.log",
    "server_optimized.log",
    "server_patched.log",
    "server_ram_optimized.log",
    "server_updated.log",
    "server_with_audio.log",
    "server_with_audio_fixed.log",
    "server_with_fallback.log",
    "server_with_models.log",
    "service1.log",
    "service2.log",
    "vlm_server.log",
    "vlm_service.log",
    "vlm_test.log",
    "web_server_langchain.log",
    "web_test.log",
    "audio_test.log",
    "audio_test2.log",
]

# Old web interface files (replaced by unified)
OLD_WEB_FILES = [
    "web_interface/index.html",  # replaced by index_unified_styled.html
    "web_interface/static/js/app.js",  # replaced by app_unified_styled.js
]

def cleanup_files(dry_run=True):
    """Remove duplicate and legacy files"""
    
    root_dir = Path(__file__).parent
    removed_count = 0
    total_size = 0
    
    print(f"{'DRY RUN: ' if dry_run else ''}Cleaning up duplicate and legacy files...\n")
    
    # Clean duplicate files
    print("1. Removing duplicate files from root directory:")
    for filename in DUPLICATE_FILES:
        filepath = root_dir / filename
        if filepath.exists():
            size = filepath.stat().st_size
            total_size += size
            removed_count += 1
            print(f"   {'Would remove' if dry_run else 'Removing'}: {filename} ({size:,} bytes)")
            if not dry_run:
                filepath.unlink()
    
    # Clean old test files
    print("\n2. Removing old test files:")
    for filename in OLD_TEST_FILES:
        filepath = root_dir / filename
        if filepath.exists():
            size = filepath.stat().st_size
            total_size += size
            removed_count += 1
            print(f"   {'Would remove' if dry_run else 'Removing'}: {filename} ({size:,} bytes)")
            if not dry_run:
                filepath.unlink()
    
    # Clean old log files
    print("\n3. Removing old log files:")
    for filename in OLD_LOG_FILES:
        filepath = root_dir / filename
        if filepath.exists():
            size = filepath.stat().st_size
            total_size += size
            removed_count += 1
            print(f"   {'Would remove' if dry_run else 'Removing'}: {filename} ({size:,} bytes)")
            if not dry_run:
                filepath.unlink()
    
    # Clean old web files
    print("\n4. Removing old web interface files:")
    for filename in OLD_WEB_FILES:
        filepath = root_dir / filename
        if filepath.exists():
            size = filepath.stat().st_size
            total_size += size
            removed_count += 1
            print(f"   {'Would remove' if dry_run else 'Removing'}: {filename} ({size:,} bytes)")
            if not dry_run:
                filepath.unlink()
    
    print(f"\nSummary:")
    print(f"{'Would remove' if dry_run else 'Removed'} {removed_count} files")
    print(f"Total space {'would be' if dry_run else ''} freed: {total_size:,} bytes ({total_size/1024/1024:.2f} MB)")
    
    if dry_run:
        print("\nRun without --dry-run to actually remove these files")
    else:
        print("\nCleanup completed!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cleanup duplicate and legacy files")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be deleted without actually deleting")
    args = parser.parse_args()
    
    cleanup_files(dry_run=args.dry_run)