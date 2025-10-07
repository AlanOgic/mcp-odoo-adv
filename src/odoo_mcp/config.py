"""
Configuration management for Odoo MCP Server
Centralized constants and environment-based configuration
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class ServerConfig:
    """MCP Server configuration with environment variable support"""

    # Smart Limits Configuration
    DEFAULT_QUERY_LIMIT: int = 100
    """Default limit for search queries when not specified"""

    MAX_QUERY_LIMIT: int = 1000
    """Maximum allowed limit for search queries (hard cap)"""

    # Cache Configuration
    SCHEMA_CACHE_SIZE: int = 128
    """Maximum number of model schemas to cache"""

    DOMAIN_CACHE_SIZE: int = 256
    """Maximum number of normalized domains to cache"""

    # Batch Operation Limits
    MAX_BATCH_SIZE: int = 100
    """Maximum number of operations in a single batch"""

    # Timeout Configuration
    DEFAULT_TIMEOUT: int = 30
    """Default timeout for Odoo API calls in seconds"""

    @classmethod
    def from_env(cls) -> "ServerConfig":
        """
        Create configuration from environment variables

        Environment Variables:
            MCP_DEFAULT_LIMIT: Default query limit (default: 100)
            MCP_MAX_LIMIT: Maximum query limit (default: 1000)
            MCP_SCHEMA_CACHE_SIZE: Schema cache size (default: 128)
            MCP_DOMAIN_CACHE_SIZE: Domain cache size (default: 256)
            MCP_MAX_BATCH_SIZE: Maximum batch size (default: 100)
            ODOO_TIMEOUT: Default timeout in seconds (default: 30)

        Returns:
            ServerConfig instance with environment-based values
        """
        return cls(
            DEFAULT_QUERY_LIMIT=int(os.getenv("MCP_DEFAULT_LIMIT", "100")),
            MAX_QUERY_LIMIT=int(os.getenv("MCP_MAX_LIMIT", "1000")),
            SCHEMA_CACHE_SIZE=int(os.getenv("MCP_SCHEMA_CACHE_SIZE", "128")),
            DOMAIN_CACHE_SIZE=int(os.getenv("MCP_DOMAIN_CACHE_SIZE", "256")),
            MAX_BATCH_SIZE=int(os.getenv("MCP_MAX_BATCH_SIZE", "100")),
            DEFAULT_TIMEOUT=int(os.getenv("ODOO_TIMEOUT", "30")),
        )

    def validate(self) -> None:
        """
        Validate configuration values

        Raises:
            ValueError: If configuration values are invalid
        """
        if self.DEFAULT_QUERY_LIMIT <= 0:
            raise ValueError("DEFAULT_QUERY_LIMIT must be positive")

        if self.MAX_QUERY_LIMIT <= 0:
            raise ValueError("MAX_QUERY_LIMIT must be positive")

        if self.DEFAULT_QUERY_LIMIT > self.MAX_QUERY_LIMIT:
            raise ValueError(
                f"DEFAULT_QUERY_LIMIT ({self.DEFAULT_QUERY_LIMIT}) "
                f"cannot exceed MAX_QUERY_LIMIT ({self.MAX_QUERY_LIMIT})"
            )

        if self.MAX_BATCH_SIZE <= 0:
            raise ValueError("MAX_BATCH_SIZE must be positive")

        if self.DEFAULT_TIMEOUT <= 0:
            raise ValueError("DEFAULT_TIMEOUT must be positive")


# Global configuration instance
config = ServerConfig.from_env()
config.validate()
