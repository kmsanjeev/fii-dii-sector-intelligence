"""Local provider authentication utility; secrets never enter stdout."""

from __future__ import annotations

import argparse
import json
import sys

from engines.providers.dhan_auth import DhanAuthError, DhanAuthManager


def main() -> int:
    parser = argparse.ArgumentParser(description="Provider-local authentication lifecycle")
    parser.add_argument("action", choices=("enroll", "status", "refresh"))
    parser.add_argument("provider", choices=("dhan",))
    args = parser.parse_args()
    manager = DhanAuthManager()
    try:
        if args.action == "enroll":
            manager.enroll_interactive()
            print(json.dumps({"provider": "dhan", "status": "ENROLLED_SECURELY"}))
        elif args.action == "status":
            state = manager.read_validation_state()
            print(json.dumps({"provider": "dhan", "credentials_configured": manager.has_credentials(), "validation_state": state}, sort_keys=True))
        else:
            token = manager.ensure_valid_token()
            print(json.dumps({"provider": "dhan", "status": "TOKEN_VALID", "expires_at": token.expires_at.isoformat()}))
    except DhanAuthError as exc:
        print(json.dumps({"provider": "dhan", "status": "BLOCKED", "code": exc.code, "http_status": exc.status_code}))
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
