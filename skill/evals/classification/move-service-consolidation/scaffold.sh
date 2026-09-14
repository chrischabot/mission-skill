#!/usr/bin/env bash
# Builds two repositories: a platform whose services call an external notification
# gateway over HTTP, and that gateway as its own git repository under external/.
set -euo pipefail

identity() {
  git config user.name "Eval Fixture"
  git config user.email "fixture@example.invalid"
  git config commit.gpgsign false
}

# The external project, in its own repository.
mkdir -p external/notify-gateway
(
  cd external/notify-gateway
  git init -q -b main .
  identity
  mkdir -p gateway tests
  printf '__pycache__/\n' > .gitignore
  cat > README.md <<'EOF'
# notify-gateway

Sends email and SMS on behalf of other services. Deployed on its own host.
Callers POST JSON to `/v1/email` or `/v1/sms` with `Authorization: Bearer <GATEWAY_TOKEN>`.
Provider keys come from `MAILER_API_KEY` and `SMS_API_KEY`.

Run the tests with `python3 -m unittest discover -s tests -t .`
EOF
  : > gateway/__init__.py
  : > tests/__init__.py
  cat > gateway/app.py <<'EOF'
import json
import os

from gateway import providers


def handle(path: str, headers: dict, body: bytes) -> tuple[int, dict]:
    expected = os.environ.get("GATEWAY_TOKEN")
    if not expected or headers.get("Authorization") != f"Bearer {expected}":
        return 401, {"error": "unauthorized"}
    payload = json.loads(body)
    if path == "/v1/email":
        return 202, providers.send_email(payload["to"], payload["subject"], payload["text"])
    if path == "/v1/sms":
        return 202, providers.send_sms(payload["to"], payload["text"])
    return 404, {"error": "not found"}
EOF
  cat > gateway/providers.py <<'EOF'
import os


def send_email(to: str, subject: str, text: str) -> dict:
    api_key = os.environ["MAILER_API_KEY"]
    # The provider HTTP call is omitted from this checkout.
    return {"provider": "mailer", "to": to, "queued": bool(api_key)}


def send_sms(to: str, text: str) -> dict:
    api_key = os.environ["SMS_API_KEY"]
    return {"provider": "sms", "to": to, "queued": bool(api_key)}
EOF
  cat > tests/test_app.py <<'EOF'
import json
import os
import unittest
from unittest import mock

from gateway.app import handle


class GatewayTest(unittest.TestCase):
    @mock.patch.dict(os.environ, {"GATEWAY_TOKEN": "t", "MAILER_API_KEY": "k"})
    def test_email_is_accepted_with_token(self):
        body = json.dumps({"to": "a@example.com", "subject": "s", "text": "x"}).encode()
        status, _ = handle("/v1/email", {"Authorization": "Bearer t"}, body)
        self.assertEqual(status, 202)

    @mock.patch.dict(os.environ, {"GATEWAY_TOKEN": "t"})
    def test_missing_token_is_rejected(self):
        self.assertEqual(handle("/v1/email", {}, b"{}")[0], 401)


if __name__ == "__main__":
    unittest.main()
EOF
  git add -A
  git commit -q -m "baseline: notify gateway"
)

# The platform, which is the working repository.
git init -q -b main .
identity
mkdir -p core/clients core/services tests

cat > .gitignore <<'EOF'
__pycache__/
external/
.drive/local/
EOF

cat > README.md <<'EOF'
# core platform

Account, billing, and invoicing services.

Notifications go through the external notify-gateway service (source checked out under
external/notify-gateway, deployed separately at `NOTIFY_GATEWAY_URL`). Platform code calls it
only through `core/clients/notify_client.py`.

Run the tests with `python3 -m unittest discover -s tests -t .`
EOF

: > core/__init__.py
: > core/clients/__init__.py
: > core/services/__init__.py
: > tests/__init__.py

cat > core/clients/notify_client.py <<'EOF'
import json
import os
import urllib.request


def send_email(to: str, subject: str, text: str) -> None:
    request = urllib.request.Request(
        os.environ["NOTIFY_GATEWAY_URL"] + "/v1/email",
        data=json.dumps({"to": to, "subject": subject, "text": text}).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {os.environ['NOTIFY_GATEWAY_TOKEN']}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    urllib.request.urlopen(request, timeout=10).close()
EOF

cat > core/services/invoices.py <<'EOF'
from core.clients import notify_client


def send_invoice(account_email: str, invoice_number: str, total: str) -> None:
    notify_client.send_email(
        account_email, f"Invoice {invoice_number}", f"Your invoice total is {total}."
    )
EOF

cat > core/services/password_reset.py <<'EOF'
from core.clients import notify_client


def send_reset_link(account_email: str, link: str) -> None:
    notify_client.send_email(account_email, "Reset your password", f"Use this link: {link}")
EOF

cat > tests/test_invoices.py <<'EOF'
import unittest
from unittest import mock

from core.services import invoices


class InvoiceTest(unittest.TestCase):
    @mock.patch("core.clients.notify_client.send_email")
    def test_invoice_email_names_the_total(self, send_email):
        invoices.send_invoice("a@example.com", "INV-7", "12.00")
        send_email.assert_called_once()
        self.assertIn("12.00", send_email.call_args.args[2])


if __name__ == "__main__":
    unittest.main()
EOF

git add -A
git commit -q -m "baseline: platform services calling the external gateway"
