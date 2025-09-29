#!/usr/bin/env python3
"""
Unified CLI for Group-1 Android App Security Scanner
Place this file in the `app/` folder and run: python app/cli.py --apk path/to/app.apk --out report.txt
"""
import argparse, sys, os, importlib

# ensure local app/ imports work when running from repo root
sys. path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def _import_attr(module, name):
    try:
        m = importlib.import_module(module)
        return getattr(m, name)
    except Exception:
        return None


def fallback_static(apk):
    if not apk:
        return [{'type':'error',' message ': ' APK provided and no scan functions found.'}]
    return [{'type':'info', 'message': f'Fallback: APK exists? {os.path.exists(apk)}'}]

def run_unified_scan(apk, package, skip_dynamic):
    report = {'metadata': {'apk': apk, 'package': package}, 'findings': []}

    # Prefer primary group scan
    if group_scan:
        try:
            # try common keyword args
            try:
                res = group_scan(apk_path=apk, package=package, dynamic=(not skip_dynamic))
            except TypeError:
                res = group_scan(apk, package)
            if isinstance(res, dict):
                # merge top-level keys
                report.update(res)
            elif isinstance(res, list):
                report['findings'].extend(res)
        except Exception as e:
            report['findings'].append({'type':'error','message': f'group_scan failed: {e}'})
    elif alt_scan:
        try:
            res = alt_scan(apk, package)
            if isinstance(res, dict):
                report.update(res)
            else:
                report['findings'].extend(res or [])
        except Exception as e:
            report['findings'].append({'type':'error','message': f'alt_scan failed: {e}'})
    else:
        report['findings'].extend(fallback_static(apk))

    # Try find_exported
    if find_exported:
        try:
            exported = find_exported(apk) if apk else find_exported(package)
            report['exported_components'] = exported
            report['findings'].append({'type':'info','message': f'Exported components found: {len(exported) if isinstance(exported, list) else exported}'})
        except Exception as e:
            report['findings'].append({'type':'warning','message': f'find_exported failed: {e}'})

    return report

def write_report(report, out_path):
    if generate_pdf:
        try:
            try:
                # common signature: generate_pdf(report_dict, out_path)
                generate_pdf(report, out_path)
                print(f"[+] PDF report written to {out_path}")
                return
            except TypeError:
                # some teams implemented generate_scan_report(out_path)
                generate_pdf(out_path)
                print(f"[+] generate_scan_report created {out_path}")
                return
        except Exception as e:
            print(f"[!] generate_scan_report failed: {e}")

    # fallback: write plain text summary
    try:
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write("Android App Security Scanner - Fallback Report\n\n")
            f.write("Metadata:\n")
            f.write(str(report.get('metadata', {})) + "\n\n")
            f.write("Findings:\n")
            for item in report.get('findings', []):
                f.write(f"- {item.get('type','?')}: {item.get('message','')}\n")
        print(f"[+] Fallback text report written to {out_path}")
    except Exception as e:
        print(f"[!] Failed to write report: {e}")

def parse_args():
    p = argparse.ArgumentParser(prog="android-scanner", description="Group-1 Android App Security Scanner")
    sub = p.add_subparsers(dest="cmd", required=False)

    # single scan mode (default)
    p.add_argument('--apk', '-a', help='Path to APK file')
    p.add_argument('--package', '-p', help='Package name for device-based checks')
    p.add_argument('--out', '-o', default='scan_report.txt', help='Path to output report')
    p.add_argument('--skip-dynamic', action='store_true', help='Skip dynamic (frida/device) checks')
    return p.parse_args()

def main():
    args = parse_args()
    report = run_unified_scan(apk=args.apk, package=args.package, skip_dynamic=args.skip_dynamic)
    write_report(report, args.out)

if __name__ == '__main__':
    main()
