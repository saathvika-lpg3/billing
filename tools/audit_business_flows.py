from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.business_flow_audit_service import BusinessFlowAuditService


def main() -> int:
    parser = argparse.ArgumentParser(description="Run read-only PRM ERP business-flow reconciliation checks.")
    parser.add_argument("--db", type=Path, default=PROJECT_ROOT / "database" / "prm_billing_inventory.db")
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT / "audit" / "business_flow_audit.json")
    args = parser.parse_args()

    result = BusinessFlowAuditService(args.db).run()
    result["generated_at"] = datetime.now().isoformat(timespec="seconds")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
