#!/usr/bin/env python3
"""
NovaSpark S3 Web Server
-----------------------
A simple HTTP server that serves static content directly from an S3 bucket.

The bucket name is read from the S3_BUCKET_NAME environment variable —
this is injected at boot time by the systemd service unit, which gets
the value from Pulumi's user_data bootstrap script.

This pattern (env var injection via systemd) is intentional: it means
the same Python script works in any environment without modification.
Pulumi simply writes a different Environment= line in the service file.
"""
import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
import boto3
from botocore.exceptions import ClientError

# Read bucket name from environment — set by systemd service unit
BUCKET_NAME = os.environ.get("S3_BUCKET_NAME", "")
PORT = int(os.environ.get("PORT", "8080"))

if not BUCKET_NAME:
    print("ERROR: S3_BUCKET_NAME environment variable is not set.")
    print("This should be injected by the systemd service.")
    sys.exit(1)

# Create the S3 client — boto3 automatically picks up IAM role credentials
# from the EC2 Instance Metadata Service (IMDS). No access keys needed here.
s3_client = boto3.client("s3", region_name="us-east-1")


class S3Handler(BaseHTTPRequestHandler):
    """Handles HTTP GET requests by fetching content from S3."""

    def do_GET(self):
        # Strip leading slash; default to index.html
        path = self.path.lstrip("/") or "index.html"

        try:
            print(f"[INFO] Fetching s3://{BUCKET_NAME}/{path}")
            response = s3_client.get_object(Bucket=BUCKET_NAME, Key=path)
            content = response["Body"].read()

            # Infer content type from file extension
            content_type = self._get_content_type(path)

            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("X-Served-From", "S3")
            self.send_header("X-Bucket", BUCKET_NAME)
            self.end_headers()
            self.wfile.write(content)

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code in ("NoSuchKey", "404"):
                self.send_error(404, f"Not found in S3: {path}")
            elif error_code in ("AccessDenied", "403"):
                # This is the error you'll see if the IAM role isn't set up correctly
                self.send_error(403, f"Access denied to s3://{BUCKET_NAME}/{path}. Check IAM role.")
            else:
                self.send_error(500, f"S3 error ({error_code}): {str(e)}")
        except Exception as e:
            self.send_error(500, f"Unexpected error: {str(e)}")

    def _get_content_type(self, path):
        if path.endswith(".html"):
            return "text/html; charset=utf-8"
        elif path.endswith(".css"):
            return "text/css"
        elif path.endswith(".js"):
            return "application/javascript"
        elif path.endswith(".json"):
            return "application/json"
        elif path.endswith(".png"):
            return "image/png"
        elif path.endswith(".jpg") or path.endswith(".jpeg"):
            return "image/jpeg"
        elif path.endswith(".svg"):
            return "image/svg+xml"
        else:
            return "text/plain"

    def log_message(self, fmt, *args):
        """Override default logging to use a cleaner format."""
        print(f"[{self.address_string()}] {fmt % args}")


def run():
    print("=" * 55)
    print("  NovaSpark S3 Web Server")
    print("=" * 55)
    print(f"  Bucket  : s3://{BUCKET_NAME}")
    print(f"  Port    : {PORT}")
    print(f"  Creds   : IAM Role (via IMDS — no keys on disk!)")
    print("=" * 55)

    server = HTTPServer(("", PORT), S3Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[INFO] Server stopped.")


if __name__ == "__main__":
    run()
