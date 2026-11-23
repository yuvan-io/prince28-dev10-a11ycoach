import argparse
import sys

import httpx


def check_health(client: httpx.Client, expected_version: str | None) -> None:
    response = client.get("/health")
    response.raise_for_status()
    data = response.json()

    version = data.get("version")
    if expected_version and version != expected_version:
        raise RuntimeError(f"Expected version {expected_version}, but got {version}")

    print(f"ok /health -> {response.status_code}, version {version}")


def check_ready(client: httpx.Client) -> None:
    response = client.get("/ready")
    response.raise_for_status()
    data = response.json()

    if data.get("status") != "ready":
        raise RuntimeError(f"Application is not ready: {data}")

    if data.get("checks", {}).get("database") is not True:
        raise RuntimeError(f"Database check failed: {data}")

    print(f"ok /ready -> {response.status_code} {data}")


def check_documents(client: httpx.Client) -> None:
    response = client.get("/v1/documents", params={"limit": 1})
    response.raise_for_status()
    print(f"ok /v1/documents?limit=1 -> {response.status_code}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke-test the A11yCoach API")
    parser.add_argument("base_url", help="Base URL, e.g. https://a11ycoach.onrender.com")
    parser.add_argument("--expect-version", help="Expected deployed Git SHA")
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")

    try:
        with httpx.Client(base_url=base_url, timeout=30.0) as client:
            check_health(client, args.expect_version)
            check_ready(client)
            check_documents(client)

        print("Smoke test passed")
        return 0
    except (httpx.HTTPError, RuntimeError, ValueError) as exc:
        print(f"Smoke test failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
