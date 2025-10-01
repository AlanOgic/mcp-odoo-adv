"""
Odoo JSON-RPC client for MCP server integration
"""

import json
import os
import sys
import re
import urllib.parse
from typing import Any, Dict, List, Optional

import requests


class OdooClient:
    """Client for interacting with Odoo via JSON-RPC"""

    def __init__(
        self,
        url,
        db,
        username,
        password,
        timeout=30,
        verify_ssl=True,
    ):
        """
        Initialize the Odoo client with connection parameters

        Args:
            url: Odoo server URL (with or without protocol)
            db: Database name
            username: Login username
            password: Login password
            timeout: Connection timeout in seconds
            verify_ssl: Whether to verify SSL certificates
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
        self.uid = None

        # Set timeout and SSL verification
        self.timeout = timeout
        self.verify_ssl = verify_ssl

        # Setup session
        self.session = requests.Session()
        self.session.verify = verify_ssl

        # HTTP proxy support
        proxy = os.environ.get("HTTP_PROXY")
        if proxy:
            self.session.proxies = {"http": proxy, "https": proxy}

        # Parse hostname for logging
        parsed_url = urllib.parse.urlparse(self.url)
        self.hostname = parsed_url.netloc

        # JSON-RPC endpoint
        self.jsonrpc_url = f"{self.url}/jsonrpc"

        # Request ID counter
        self._request_id = 0

        # Connect
        self._connect()

    def _jsonrpc_call(self, service: str, method: str, *args) -> Any:
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
            "params": {
                "service": service,
                "method": method,
                "args": list(args)
            },
            "id": self._request_id
        }

        try:
            response = self.session.post(
                self.jsonrpc_url,
                json=payload,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"}
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

    def _connect(self):
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

    def _execute(self, model, method, *args, **kwargs):
        """Execute a method on an Odoo model using JSON-RPC"""
        return self._jsonrpc_call(
            "object", "execute_kw",
            self.db, self.uid, self.password,
            model, method, args, kwargs
        )

    def execute_method(self, model, method, *args, **kwargs):
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

    def get_models(self):
        """
        Get a list of all available models in the system

        Returns:
            List of model names

        Examples:
            >>> client = OdooClient(url, db, username, password)
            >>> models = client.get_models()
            >>> print(len(models))
            125
            >>> print(models[:5])
            ['res.partner', 'res.users', 'res.company', 'res.groups', 'ir.model']
        """
        try:
            # First search for model IDs
            model_ids = self._execute("ir.model", "search", [])

            if not model_ids:
                return {
                    "model_names": [],
                    "models_details": {},
                    "error": "No models found",
                }

            # Then read the model data with only the most basic fields
            # that are guaranteed to exist in all Odoo versions
            result = self._execute("ir.model", "read", model_ids, ["model", "name"])

            # Extract and sort model names alphabetically
            models = sorted([rec["model"] for rec in result])

            # For more detailed information, include the full records
            models_info = {
                "model_names": models,
                "models_details": {
                    rec["model"]: {"name": rec.get("name", "")} for rec in result
                },
            }

            return models_info
        except Exception as e:
            print(f"Error retrieving models: {str(e)}", file=sys.stderr)
            return {"model_names": [], "models_details": {}, "error": str(e)}

    def get_model_info(self, model_name):
        """
        Get information about a specific model

        Args:
            model_name: Name of the model (e.g., 'res.partner')

        Returns:
            Dictionary with model information

        Examples:
            >>> client = OdooClient(url, db, username, password)
            >>> info = client.get_model_info('res.partner')
            >>> print(info['name'])
            'Contact'
        """
        try:
            result = self._execute(
                "ir.model",
                "search_read",
                [("model", "=", model_name)],
                {"fields": ["name", "model"]},
            )

            if not result:
                return {"error": f"Model {model_name} not found"}

            return result[0]
        except Exception as e:
            print(f"Error retrieving model info: {str(e)}", file=sys.stderr)
            return {"error": str(e)}

    def get_model_fields(self, model_name):
        """
        Get field definitions for a specific model

        Args:
            model_name: Name of the model (e.g., 'res.partner')

        Returns:
            Dictionary mapping field names to their definitions

        Examples:
            >>> client = OdooClient(url, db, username, password)
            >>> fields = client.get_model_fields('res.partner')
            >>> print(fields['name']['type'])
            'char'
        """
        try:
            fields = self._execute(model_name, "fields_get")
            return fields
        except Exception as e:
            print(f"Error retrieving fields: {str(e)}", file=sys.stderr)
            return {"error": str(e)}

    def search_read(
        self, model_name, domain, fields=None, offset=None, limit=None, order=None
    ):
        """
        Search for records and read their data in a single call

        Args:
            model_name: Name of the model (e.g., 'res.partner')
            domain: Search domain (e.g., [('is_company', '=', True)])
            fields: List of field names to return (None for all)
            offset: Number of records to skip
            limit: Maximum number of records to return
            order: Sorting criteria (e.g., 'name ASC, id DESC')

        Returns:
            List of dictionaries with the matching records

        Examples:
            >>> client = OdooClient(url, db, username, password)
            >>> records = client.search_read('res.partner', [('is_company', '=', True)], limit=5)
            >>> print(len(records))
            5
        """
        try:
            kwargs = {}
            if offset:
                kwargs["offset"] = offset
            if fields is not None:
                kwargs["fields"] = fields
            if limit is not None:
                kwargs["limit"] = limit
            if order is not None:
                kwargs["order"] = order

            result = self._execute(model_name, "search_read", domain, **kwargs)
            return result
        except Exception as e:
            print(f"Error in search_read: {str(e)}", file=sys.stderr)
            return []

    def read_records(self, model_name, ids, fields=None):
        """
        Read data of records by IDs

        Args:
            model_name: Name of the model (e.g., 'res.partner')
            ids: List of record IDs to read
            fields: List of field names to return (None for all)

        Returns:
            List of dictionaries with the requested records

        Examples:
            >>> client = OdooClient(url, db, username, password)
            >>> records = client.read_records('res.partner', [1])
            >>> print(records[0]['name'])
            'YourCompany'
        """
        try:
            kwargs = {}
            if fields is not None:
                kwargs["fields"] = fields

            result = self._execute(model_name, "read", ids, kwargs)
            return result
        except Exception as e:
            print(f"Error reading records: {str(e)}", file=sys.stderr)
            return []


def load_config():
    """
    Load Odoo configuration from environment variables or config file

    Returns:
        dict: Configuration dictionary with url, db, username, password
    """
    # Define config file paths to check
    config_paths = [
        "./odoo_config.json",
        os.path.expanduser("~/.config/odoo/config.json"),
        os.path.expanduser("~/.odoo_config.json"),
    ]

    # Try environment variables first
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

    # Try to load from file
    for path in config_paths:
        expanded_path = os.path.expanduser(path)
        if os.path.exists(expanded_path):
            with open(expanded_path, "r") as f:
                return json.load(f)

    raise FileNotFoundError(
        "No Odoo configuration found. Please create an odoo_config.json file or set environment variables."
    )


def get_odoo_client():
    """
    Get a configured Odoo client instance

    Returns:
        OdooClient: A configured Odoo client instance
    """
    config = load_config()

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
    print(f"  Timeout: {timeout}s", file=sys.stderr)
    print(f"  Verify SSL: {verify_ssl}", file=sys.stderr)

    return OdooClient(
        url=config["url"],
        db=config["db"],
        username=config["username"],
        password=config["password"],
        timeout=timeout,
        verify_ssl=verify_ssl,
    )
