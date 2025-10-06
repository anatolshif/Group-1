#!/usr/bin/env python3
"""
Unified CLI for Group-1 Android App Security Scanner

This script orchestrates the full mobile security analysis workflow,
including static analysis, dynamic checks, data extraction, and report generation.

Usage:
    python cli.py --apk path/to/app.apk --out report.pdf

To skip dynamic checks (no device needed):
    python cli.py -a path/to/app.apk -p com.target.app --skip-dynamic -o static_report.pdf
"""
import argparse
import sys
import os
import importlib
import json
import traceback
import datetime

# Ensure local app/ imports work when running from repo root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# --- Helper: Dynamic attribute importer ---
def _import_attr(module, name):
    """Safely import an attribute (function/class) from a module file.

    Returns the attribute or None if import fails.
    """
    try:
        m = importlib.import_module(module)
        return getattr(m, name)
    except Exception:
        # Could log/debug here; return None to allow graceful fallback
        return None

# --- Module Loader ---
# Dynamically load key functions from other files (may return None if module missing)
group_scan = _import_attr('group_scan_main', 'group_scan')          # Assumed primary wrapper
alt_scan = _import_attr('alt_group1proj', 'group_scan')            # Fallback/Alternative main
find_exported = _import_attr('find_exported', 'find_exported_true')# From existing static check
generate_pdf = _import_attr('generate_scan_report', 'build_pdf')   # PDF generator

def fallback_static(apk):
    """Simple fallback if no main scanning function is found."""
    if not apk:
        return [{'type': 'error', 'message': 'No APK provided and no scan functions found.'}]
    return [{'type': 'info', 'message': 'Fallback: APK provided. Static analysis must be run via sub-modules.'}]

def run_unified_scan(apk, package, skip_dynamic):
    """Executes the full scan pipeline: Static, Dynamic, and Data Extraction."""

    report = {
        'metadata': {'apk': apk, 'package': package, 'scanner_version': 'v0.5'},
        'findings': [],
        'summary': {'High': 0, 'Medium': 0, 'Low': 0, 'total_checks': 0, 'issues_found': 0}
    }

    # ---------------------------------------------
    # 1. Primary Group Scan (Integrates most checks)
    # ---------------------------------------------
    print("[STEP 1] Running main scan logic...")
    if group_scan or alt_scan:
        try:
            scan_func = group_scan if group_scan else alt_scan

            # Use kwargs matching the expected signature of a robust scan function
            res = scan_func(
                apk_path=apk,
                package=package,
                dynamic=(not skip_dynamic),
                run_data_extraction=(not skip_dynamic)
            )

            # Merge results safely
            if isinstance(res, dict):
                # Expecting possible top-level keys: metadata, findings, summary
                if 'metadata' in res and isinstance(res['metadata'], dict):
                    report['metadata'].update(res['metadata'])
                if 'summary' in res and isinstance(res['summary'], dict):
                    report['summary'].update(res['summary'])
                if 'findings' in res and isinstance(res['findings'], list):
                    report['findings'].extend(res['findings'])
                # Merge any other keys at top level
                for k, v in res.items():
                    if k not in ('metadata', 'summary', 'findings'):
                        report[k] = v
            elif isinstance(res, list):
                report['findings'].extend(res)
            else:
                # unknown type: add as info
                report['findings'].append({'type': 'info', 'message': f'Main scan returned unsupported type: {type(res).__name__}'})

        except Exception as e:
            report['findings'].append({'type': 'error', 'message': f'Main scan failed: {type(e).__name__}: {e}'})
            # traceback.print_exc()  # Uncomment for debugging
    else:
        # Fallback if the main scan function doesn't exist
        report['findings'].extend(fallback_static(apk))

    # ---------------------------------------------
    # 2. Static Check - Exported Components (Redundant check if done in group_scan)
    # ---------------------------------------------
    if find_exported:
        print("[STEP 2] Running Exported Components check...")
        try:
            # Assumes find_exported takes the APK path
            exported = find_exported(apk)
            if isinstance(exported, list):
                report['exported_components'] = exported
                report['findings'].append({'type': 'info', 'message': f'Exported components found: {len(exported)}'})
            else:
                report['findings'].append({'type': 'info', 'message': f'Exported component check summary: {exported}'})
        except Exception as e:
            report['findings'].append({'type': 'warning', 'message': f'find_exported failed: {e}'})

    return report

def write_report(report, out_path):
    """Writes the final report, prioritizing PDF generation."""
    print(f"[STEP 3] Generating report: {out_path}")

    # 1. Try PDF generation (Requires generate_scan_report.py to be present)
    if generate_pdf and out_path.lower().endswith('.pdf'):
        # Create a temporary JSON file to hold the results for the PDF generator
        temp_json_path = out_path.replace(".pdf", ".temp.json")
        try:
            with open(temp_json_path, 'w', encoding='utf-8') as f:
                # Clean up report structure to match expected PDF input format
                final_report_data = {
                    "app_name": report['metadata'].get('package', 'Unknown App'),
                    "package": report['metadata'].get('package', 'N/A'),
                    "scan_date": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    "scanner_version": report['metadata'].get('scanner_version', 'v0.5'),
                    "summary": report.get('summary', {}),
                    "vulnerabilities": report.get('findings', [])  # Mapping generic 'findings' to 'vulnerabilities'
                }
                json.dump(final_report_data, f, indent=2)

            # Call PDF generator
            generate_pdf(temp_json_path, out_path)
            print(f"[+] PDF report successfully written to {out_path}")
            # Optionally remove temp file
            # os.remove(temp_json_path)
            return
        except Exception as e:
            print(f"[!] PDF report generation failed. Falling back to JSON/Text: {e}")
            # traceback.print_exc()  # Uncomment for debugging

    # 2. Fallback: Write full JSON output
    try:
        # Ensure extension is .json
        base, ext = os.path.splitext(out_path)
        json_path = out_path if ext.lower() == '.json' else f"{base}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=4)
        print(f"[+] JSON report written to {json_path}")
    except Exception as e:
        print(f"[!] Failed to write fallback JSON report: {e}")

def parse_args():
    """Defines and parses the command-line arguments, including the help text."""

    p = argparse.ArgumentParser(
        prog="android-scanner",
        description=(
            "Group-1 Android App Security Scanner: Automated tool for static and dynamic analysis "
            "of Android applications based on the OWASP Mobile Top 10.\n"
            "Requires ADB and optionally Frida for dynamic checks."
        ),
        formatter_class=argparse.RawTextHelpFormatter
    )

    # Required inputs (but we validate at runtime; not enforcing argparse 'required' to allow flexibility)
    p.add_argument(
        '--apk',
        '-a',
        help=(
            'Path to the target APK file. (Required for Static Analysis: Manifest checks, '
            'permissions analysis, Flutter detection, and component extraction).'
        )
    )
    p.add_argument(
        '--package',
        '-p',
        help=(
            'Package name of the target app (e.g., com.example.app).\n'
            'Required for Dynamic Checks: Log capture, Frida hooks (SSL bypass), '
            'and automated data extraction (databases/prefs).'
        )
    )

    # Optional flags
    p.add_argument(
        '--out',
        '-o',
        default='scan_report.pdf',
        help='Path for the output report (e.g., scan_report.pdf or scan_results.json).'
    )
    p.add_argument(
        '--skip-dynamic',
        action='store_true',
        help=(
            'Skip all dynamic checks (Frida instrumentation, log capture, and data extraction).\n'
            'Only static analysis will be performed. Useful when no device is connected.'
        )
    )

    return p.parse_args()

def main():
    args = parse_args()

    # Validate arguments
    # If user explicitly skips dynamic checks, apk is required (static only)
    if args.skip_dynamic and not args.apk:
        print("Error: --skip-dynamic requires --apk for static analysis.")
        sys.exit(1)

    # If dynamic checks are not skipped, require at least apk or package to do something useful
    if not args.skip_dynamic and not (args.apk or args.package):
        print("Error: Provide at least --apk (for static) or --package (for dynamic).")
        sys.exit(1)

    report = run_unified_scan(apk=args.apk, package=args.package, skip_dynamic=args.skip_dynamic)

    write_report(report, args.out)

if __name__ == '__main__':
    main()

