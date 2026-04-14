#!/usr/bin/env python3
"""
Shared utilities for MiniMax API tools.
"""

import os
import time
import requests


def resolve_api_key(api_key: str = None) -> str:
    """Resolves API key from argument or environment variable."""
    if api_key:
        return api_key
    env_key = os.environ.get("MINIMAX_API_KEY") or os.environ.get("MINIMAX_API_TOKEN")
    if env_key:
        return env_key
    return None


def sanitize_filename(name: str) -> str:
    """Removes invalid characters from a filename."""
    keepcharacters = " ._-"
    return "".join(c for c in name if c.isalnum() or c in keepcharacters).strip()


def poll_task_status(
    api_key: str,
    status_url: str,
    poll_interval: int = 10,
    max_retries: int = 100,
    timeout_seconds: int = 3600,
) -> dict:
    """
    Polls task status until success, failure, or timeout.

    Args:
        api_key: API key for authentication
        status_url: URL to poll for status
        poll_interval: Seconds between polls
        max_retries: Maximum number of polls (default 100)
        timeout_seconds: Maximum time to wait (default 1 hour)

    Returns:
        dict with status info including file_id on success

    Raises:
        Exception: If task fails or timeout reached
    """
    headers = {"Authorization": f"Bearer {api_key}"}
    start_time = time.time()
    retries = 0

    while retries < max_retries:
        elapsed = time.time() - start_time
        if elapsed > timeout_seconds:
            raise Exception(f"Polling timeout reached ({timeout_seconds}s)")

        time.sleep(poll_interval)

        try:
            response = requests.get(status_url, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            raise Exception(f"Polling request failed: {e}")

        status = data.get("status")
        print(f"  Status: {status}")

        if status == "Success":
            return data
        elif status == "Fail":
            raise Exception(
                f"Task failed: {data.get('error_message', 'Unknown error')}"
            )

        retries += 1

    raise Exception(f"Max retries ({max_retries}) exceeded")


def retry_api_call(func, max_retries: int = 3, delay: int = 5):
    """
    Retries an API call with exponential backoff.

    Args:
        func: Function to call
        max_retries: Maximum number of retries
        delay: Initial delay between retries in seconds

    Returns:
        Response from func

    Raises:
        Last exception if all retries fail
    """
    last_error = None
    for attempt in range(max_retries):
        try:
            return func()
        except requests.RequestException as e:
            last_error = e
            if attempt < max_retries - 1:
                wait_time = delay * (2**attempt)
                print(f"  Retry {attempt + 1}/{max_retries} after {wait_time}s...")
                time.sleep(wait_time)
    raise last_error
