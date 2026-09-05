"""
Odoo JSON-RPC client for MCP server integration
"""

import json
import os
import re
import sys
import urllib.parse
from functools import lru_cache
from typing import Any, Dict, Optional

import requests
from dotenv import load_dotenv


class OdooClient:
    """Client for interacting with Odoo via JSON-RPC or JSON-2 API"""

    def __init__(
        self,
        url: str,
        db: str,
        username: str,
        password: Optional[str] = None,
        api_key: Optional[str] = None,
        api_version: str = "json-rpc",
        timeout: int = 30,
        verify_ssl: bool = True,
    ) -> None:
        """
        Initialize the Odoo client with connection parameters

        Args:
            url: Odoo server URL (with or without protocol)
            db: Database name
            username: Login username
            password: Login password or API key (JSON-RPC path, Odoo 14-18)
            api_key: Bearer token for JSON-2 API (Odoo 19+ only)
            api_version: "json-rpc" (default, Odoo 14-18) or "json-2" (Odoo 19+)
            timeout: Connection timeout in seconds
            verify_ssl: Whether to verify SSL certificates

        Note:
            - Odoo 18 is the primary target: use JSON-RPC with an API key in
              the password field for better security than a raw password.
            - JSON-2 is an opt-in upgrade available only on Odoo 19+.
            - JSON-RPC will be removed in Odoo 20 (fall 2026).
        """
        # Ensure URL has a protocol
        if not re.match(r"^https?://", url):
            url = f"http://{url}"

        # Remove trailing slash from URL if present
        url = url.rstrip("/")

        self.url = url
        self.db = db
        self.username = username
        self.password = password
        self.api_key = api_key
        self.api_version = api_version
        self.uid = None

        # Validate API version and credentials
        if api_version == "json-2":
            if not api_key:
                raise ValueError("api_key is required for JSON-2 API (Odoo 19+)")
        else:  # json-rpc
            if not password:
                raise ValueError("password is required for JSON-RPC API")

        # Set timeout and SSL verification
        self.timeout = timeout
        self.verify_ssl = verify_ssl

        # Setup session
        self.session = requests.Session()
        self.session.verify = verify_ssl

        # Configure headers for JSON-2 API
        if api_version == "json-2":
            self.session.headers["Authorization"] = f"Bearer {api_key}"
            self.session.headers["X-Odoo-Database"] = db
            self.session.headers["Content-Type"] = "application/json"

        # HTTP proxy support
        proxy = os.environ.get("HTTP_PROXY")
        if proxy:
            self.session.proxies = {"http": proxy, "https": proxy}

        # Parse hostname for logging
        parsed_url = urllib.parse.urlparse(self.url)
        self.hostname = parsed_url.netloc

        # JSON-RPC endpoint (for legacy API)
        self.jsonrpc_url = f"{self.url}/jsonrpc"

        # JSON-2 API base URL
        self.json2_base_url = f"{self.url}/api/v2"

        # Request ID counter (for JSON-RPC)
        self._request_id = 0

        # Connect (only for JSON-RPC, JSON-2 uses Bearer token)
        if api_version == "json-rpc":
            self._connect()

    def _jsonrpc_call(self, service: str, method: str, *args: Any) -> Any:
        """
        Make a JSON-RPC 1.x call to Odoo

        Args:
            service: Service name ('common' or 'object')
            method: Method name to call
            *args: Arguments to pass to the method

        Returns:
            Result of the method call
        """
        self._request_id += 1

        payload = {
            "jsonrpc": "1.0",
            "method": "call",
            "params": {"service": service, "method": method, "args": list(args)},
            "id": self._request_id,
        }

        try:
            response = self.session.post(
                self.jsonrpc_url,
                json=payload,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()

            result = response.json()

            if "error" in result:
                error_data = result["error"]
                error_msg = error_data.get("data", {}).get("message", str(error_data))
                raise ValueError(f"Odoo error: {error_msg}")

            return result.get("result")

        except requests.exceptions.Timeout as e:
            raise TimeoutError(f"Request timeout after {self.timeout}s: {str(e)}")
        except requests.exceptions.ConnectionError as e:
            raise ConnectionError(f"Failed to connect to Odoo server: {str(e)}")
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Request failed: {str(e)}")

    def _connect(self) -> None:
        """Initialize the JSON-RPC connection and authenticate"""
        print(f"Connecting to Odoo at: {self.url}", file=sys.stderr)
        print(f"  Hostname: {self.hostname}", file=sys.stderr)
        print(
            f"  Timeout: {self.timeout}s, Verify SSL: {self.verify_ssl}",
            file=sys.stderr,
        )
        print(f"  JSON-RPC endpoint: {self.jsonrpc_url}", file=sys.stderr)

        # Authenticate and get user ID
        print(
            f"Authenticating with database: {self.db}, username: {self.username}",
            file=sys.stderr,
        )
        try:
            self.uid = self._jsonrpc_call(
                "common", "authenticate", self.db, self.username, self.password, {}
            )
            if not self.uid:
                raise ValueError("Authentication failed: Invalid username or password")

            print(f"  Authenticated successfully with UID: {self.uid}", file=sys.stderr)

        except (TimeoutError, ConnectionError) as e:
            print(f"Connection error: {str(e)}", file=sys.stderr)
            raise
        except Exception as e:
            print(f"Authentication error: {str(e)}", file=sys.stderr)
            raise ValueError(f"Failed to authenticate with Odoo: {str(e)}")

    def _execute(self, model: str, method: str, *args: Any, **kwargs: Any) -> Any:
        """Execute a method on an Odoo model using JSON-RPC or JSON-2 API"""
        if self.api_version == "json-2":
            # JSON-2 API format
            url = f"{self.json2_base_url}/{model}/{method}"
            payload = {
                "args": list(args) if args else [],
                "kwargs": kwargs if kwargs else {},
            }

            try:
                response = self.session.post(url, json=payload, timeout=self.timeout)
                response.raise_for_status()
                return response.json()

            except requests.exceptions.Timeout as e:
                raise TimeoutError(f"Request timeout after {self.timeout}s: {str(e)}")
            except requests.exceptions.ConnectionError as e:
                raise ConnectionError(f"Failed to connect to Odoo server: {str(e)}")
            except requests.exceptions.RequestException as e:
                raise ValueError(f"Request failed: {str(e)}")
        else:
            # JSON-RPC format (legacy)
            return self._jsonrpc_call(
                "object",
                "execute_kw",
                self.db,
                self.uid,
                self.password,
                model,
                method,
                args,
                kwargs,
            )

    def execute_method(self, model: str, method: str, *args: Any, **kwargs: Any) -> Any:
        """
        Execute an arbitrary method on a model

        Args:
            model: The model name (e.g., 'res.partner')
            method: Method name to execute
            *args: Positional arguments to pass to the method
            **kwargs: Keyword arguments to pass to the method

        Returns:
            Result of the method execution
        """
        return self._execute(model, method, *args, **kwargs)


def load_config() -> Dict[str, Any]:
    """
    Load Odoo configuration from .env file, environment variables, or config file

    Priority order:
    1. Search for .env file in common locations and load it
    2. Check environment variables (may have been set by .env)
    3. Fall back to JSON config files

    Environment Variables:
        ODOO_CONFIG_DIR: Custom directory to search for .env file (highest priority)

    Returns:
        dict: Configuration dictionary with url, db, username, password
    """
    # Define .env file paths to check (in priority order)
    env_paths = []

    # Check for custom config directory (highest priority)
    custom_config_dir = os.environ.get("ODOO_CONFIG_DIR")
    if custom_config_dir:
        custom_env_path = os.path.join(os.path.expanduser(custom_config_dir), ".env")
        env_paths.append(custom_env_path)

    # Standard paths
    env_paths.extend(
        [
            ".env",  # Current directory
            os.path.expanduser("~/.config/odoo/.env"),  # User config directory
            os.path.expanduser("~/.env"),  # User home directory
        ]
    )

    # Try to load .env file from common locations
    for env_path in env_paths:
        expanded_path = os.path.expanduser(env_path)
        if os.path.exists(expanded_path):
            print(f"Loading configuration from: {expanded_path}", file=sys.stderr)
            load_dotenv(dotenv_path=expanded_path, override=True)
            break

    # Check environment variables (may have been set by .env file)
    if all(
        var in os.environ
        for var in ["ODOO_URL", "ODOO_DB", "ODOO_USERNAME", "ODOO_PASSWORD"]
    ):
        return {
            "url": os.environ["ODOO_URL"],
            "db": os.environ["ODOO_DB"],
            "username": os.environ["ODOO_USERNAME"],
            "password": os.environ["ODOO_PASSWORD"],
        }

    # Fall back to JSON config files
    config_paths = [
        "./odoo_config.json",
        os.path.expanduser("~/.config/odoo/config.json"),
        os.path.expanduser("~/.odoo_config.json"),
    ]

    for path in config_paths:
        expanded_path = os.path.expanduser(path)
        if os.path.exists(expanded_path):
            print(f"Loading configuration from: {expanded_path}", file=sys.stderr)
            with open(expanded_path, "r") as f:
                loaded: Dict[str, Any] = json.load(f)
            return loaded

    raise FileNotFoundError(
        "No Odoo configuration found. Please create a .env file, set environment variables, or create an odoo_config.json file.\n"
        "Searched for .env in:\n  " + "\n  ".join(env_paths) + "\n"
        "Searched for JSON config in:\n  " + "\n  ".join(config_paths)
    )


@lru_cache(maxsize=1)
def get_odoo_client() -> OdooClient:
    """
    Get the singleton Odoo client instance.

    Cached for the process lifetime — the first call builds the client
    (including the JSON-RPC authenticate round-trip), subsequent calls
    return the same instance. Call ``get_odoo_client.cache_clear()`` to
    force a rebuild (tests only).

    Supports both JSON-RPC (Odoo 14-18) and JSON-2 API (Odoo 19+).

    Environment variables:
        ODOO_API_VERSION: "json-rpc" (default) or "json-2"
        ODOO_API_KEY: API key for JSON-2 (Bearer token)
        ODOO_PASSWORD: Password or API key for JSON-RPC

    Returns:
        OdooClient: A configured Odoo client instance
    """
    config = load_config()

    # Get API version preference
    api_version = os.environ.get("ODOO_API_VERSION", "json-rpc").lower()

    # Get authentication credentials
    api_key = os.environ.get("ODOO_API_KEY")
    password = config.get("password") or os.environ.get("ODOO_PASSWORD")

    # Get additional options from environment variables
    timeout = int(
        os.environ.get("ODOO_TIMEOUT", "30")
    )  # Increase default timeout to 30 seconds
    verify_ssl = os.environ.get("ODOO_VERIFY_SSL", "1").lower() in ["1", "true", "yes"]

    # Print detailed configuration
    print("Odoo client configuration:", file=sys.stderr)
    print(f"  URL: {config['url']}", file=sys.stderr)
    print(f"  Database: {config['db']}", file=sys.stderr)
    print(f"  Username: {config['username']}", file=sys.stderr)
    print(f"  API Version: {api_version}", file=sys.stderr)
    if api_version == "json-2":
        print(f"  Auth: API Key ({'set' if api_key else 'NOT SET'})", file=sys.stderr)
    else:
        print(f"  Auth: Password ({'set' if password else 'NOT SET'})", file=sys.stderr)
    print(f"  Timeout: {timeout}s", file=sys.stderr)
    print(f"  Verify SSL: {verify_ssl}", file=sys.stderr)

    return OdooClient(
        url=config["url"],
        db=config["db"],
        username=config["username"],
        password=password,
        api_key=api_key,
        api_version=api_version,
        timeout=timeout,
        verify_ssl=verify_ssl,
    )
