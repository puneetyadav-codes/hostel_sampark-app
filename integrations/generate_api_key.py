import argparse
import hashlib
import json
import re
import secrets


SCOPES = ("grievance:submit", "grievance:status")


def main():
    parser = argparse.ArgumentParser(
        description="Generate a one-time platform API key and its Render config."
    )
    parser.add_argument(
        "client_id",
        help="A short name for the connected service, for example campus_portal.",
    )
    parser.add_argument(
        "scopes",
        nargs="+",
        choices=SCOPES,
        help="Allowed actions for this key.",
    )
    args = parser.parse_args()

    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", args.client_id):
        parser.error("client_id may contain only letters, numbers, underscores, and hyphens.")

    token = secrets.token_urlsafe(32)
    key_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    entry = {
        args.client_id: {
            "key_hash": key_hash,
            "scopes": sorted(set(args.scopes)),
        }
    }

    print("Copy this private API key now; it will not be shown again:")
    print(token)
    print("\nAdd this client entry to the PLATFORM_API_KEYS_JSON value in Render:")
    print(json.dumps(entry, separators=(",", ":")))
    print("\nStore the private API key only in the connected platform's server settings.")


if __name__ == "__main__":
    main()
