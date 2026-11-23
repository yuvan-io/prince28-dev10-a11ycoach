import argparse
import sys
import time

import httpx


def wait_for_health(
    client: httpx.Client,
    expected_version: str | None,
    timeout: int,
    interval: int,
) -> None:
    """Wait until the expected application version is live."""
    deadline = time.monotonic() + timeout
    last_error: Exception | None = None

    while True:
        try:
            response = client.get("/health")
            response.raise_for_status()
            data = response.json()

            version = data.get("version")

            if expected_version is None or version == expected_version:
                print(f"ok /health -> {response.status_code}, version {version}")
                return

            last_error = RuntimeError(f"Expected version {expected_version}, but got {version}")

        except (httpx.HTTPError, ValueError) as exc:
            last_error = exc

        remaining = deadline - time.monotonic()

        if remaining <= 0:
            raise RuntimeError(
                f"Health check timed out after {timeout} seconds. Last result: {last_error}"
            ) from last_error

        print(
            f"Waiting for expected version. Retrying in {min(interval, remaining):.0f} seconds..."
        )
        time.sleep(min(interval, remaining))


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
    parser.add_argument(
        "base_url",
        help="Base URL, e.g. https://a11ycoach.onrender.com",
    )
    parser.add_argument("--expect-version", help="Expected deployed Git SHA")
    parser.add_argument(
        "--wait-timeout",
        type=int,
        default=300,
        help="Maximum seconds to wait for the expected version (default: 300)",
    )
    parser.add_argument(
        "--poll-interval",
        type=int,
        default=10,
        help="Seconds between health-check attempts (default: 10)",
    )
    args = parser.parse_args()

    if args.wait_timeout <= 0 or args.poll_interval <= 0:
        parser.error("--wait-timeout and --poll-interval must be positive")

    base_url = args.base_url.rstrip("/")

    try:
        with httpx.Client(base_url=base_url, timeout=30.0) as client:
            wait_for_health(
                client,
                args.expect_version,
                args.wait_timeout,
                args.poll_interval,
            )
            check_ready(client)
            check_documents(client)

        print("Smoke test passed")
        return 0

    except (httpx.HTTPError, RuntimeError, ValueError) as exc:
        print(f"Smoke test failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
