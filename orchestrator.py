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
import argparse, sys, os, importlib
import json
import traceback

# Ensure local app/ imports work when running from repo root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# --- Module Loader ---
# Dynamically load key functions from other files
group_scan = _import_attr('group_scan_main', 'group_scan') # Assumed primary wrapper
alt_scan = _import_attr('alt_group1proj', 'group_scan') # Fallback/Alternative main
find_exported = _import_attr('find_exported', 'find_exported_true') # From existing static check
generate_pdf = _import_attr('generate_scan_report', 'build_pdf')

def _import_attr(module, name):
    """Safely import an attribute (function) from a module file."""
    try:
        # Assuming all module files are in the same 'app/' directory or PYTHONPATH
        m = importlib.import_module(module)
        return getattr(m, name)
    except Exception:
        # print(f"Warning: Could not import {name} from {module}.")
        return None


def fallback_static(apk):
    """Simple fallback if no main scanning function is found."""
    if not apk:
        return [{'type':'error','message': 'No APK provided and no scan functions found.'}]
    return [{'type':'info', 'message': f'Fallback: APK provided. Static analysis must be run via sub-modules.'}]

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

            if isinstance(res, dict):
                report.update(res) # Merge top-level keys (metadata, findings, summary)
            elif isinstance(res, list):
                report['findings'].extend(res)
            
        except Exception as e:
            report['findings'].append({'type':'error','message': f'Main scan failed: {type(e).__name__}: {e}'})
            # traceback.print_exc() # Useful for debugging

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
                report['findings'].append({'type':'info','message': f'Exported components found: {len(exported)}'})
            else:
                 report['findings'].append({'type':'info','message': f'Exported component check summary: {exported}'})
        except Exception as e:
            report['findings'].append({'type':'warning','message': f'find_exported failed: {e}'})

    return report

def write_report(report, out_path):
    """Writes the final report, prioritizing PDF generation."""
    print(f"[STEP 3] Generating report: {out_path}")
    
    # 1. Try PDF generation (Requires generate_scan_report.py to be present)
    if generate_pdf:
        # Create a temporary JSON file to hold the results for the PDF generator
        temp_json_path = out_path.replace(".pdf", ".temp.json")
        try:
            with open(temp_json_path, 'w', encoding='utf-8') as f:
                 # Clean up report structure to match expected PDF input format
                 final_report_data = {
                    "app_name": report['metadata'].get('package', 'Unknown App'),
                    "package": report['metadata'].get('package', 'N/A'),
                    "scan_date": datetime.datetime.now(datetime.UTC).isoformat(),
                    "scanner_version": report['metadata'].get('scanner_version', 'v0.5'),
                    "summary": report.get('summary', {}),
                    "vulnerabilities": report.get('findings', []) # Mapping generic 'findings' to 'vulnerabilities'
                 }
                 json.dump(final_report_data, f, indent=2)
            
            generate_pdf(temp_json_path, out_path)
            print(f"[+] PDF report successfully written to {out_path}")
            # os.remove(temp_json_path) # Clean up temp file
            return
        except Exception as e:
            print(f"[!] PDF report generation failed. Falling back to JSON/Text: {e}")
            # traceback.print_exc() # Useful for debugging

    # 2. Fallback: Write full JSON output
    try:
        json_path = out_path if out_path.lower().endswith('.json') else out_path.replace(os.path.splitext(out_path)[1], '.json')
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

    # Required inputs
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
    
    # Check for minimal arguments required to run the core unified scan
    if not args.apk and not args.package:
        if args.skip_dynamic:
             print("Error: Must provide --apk for static analysis or --package for dynamic analysis.")
        else:
            print("Error: Must provide at least --apk (for static) or --package (for dynamic).")
            
        sys.exit(1)
        
    report = run_unified_scan(apk=args.apk, package=args.package, skip_dynamic=args.skip_dynamic)
    
    write_report(report, args.out)

if __name__ == '__main__':
    import datetime
    main()
