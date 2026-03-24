"""
Azure Key Vault secrets manager for Django.

Retrieves secrets from Azure Key Vault with fallback to environment variables.
Used for secure configuration management in production and development.
"""

import os
import logging
from typing import Optional, Dict, Any
from functools import lru_cache

logger = logging.getLogger(__name__)


class SecretsManager:
    """
    Manages retrieval of secrets from Azure Key Vault or environment variables.
    
    Priority order:
    1. Azure Key Vault (if configured)
    2. Environment variables
    3. Default value (if provided)
    
    Example:
        secrets = SecretsManager()
        db_password = secrets.get("POSTGRES_PASSWORD")
        secret_key = secrets.get("SECRET_KEY", default="dev-only-key")
    """
    
    def __init__(self, use_key_vault: bool = True):
        """
        Initialize the secrets manager.
        
        Args:
            use_key_vault: Whether to attempt Key Vault connection.
                          Set to False for environments without Azure credentials.
        """
        self.use_key_vault = use_key_vault
        self._client = None
        self._initialized = False
        self._initialization_error = None
        
        if self.use_key_vault:
            self._init_key_vault_client()
    
    def _init_key_vault_client(self) -> None:
        """Initialize Azure Key Vault client if credentials are available."""
        try:
            from azure.identity import DefaultAzureCredential
            from azure.keyvault.secrets import SecretClient
            
            key_vault_url = os.getenv("AZURE_KEY_VAULT_URL")
            
            if not key_vault_url:
                logger.warning(
                    "AZURE_KEY_VAULT_URL not set. Will use environment variables only."
                )
                self.use_key_vault = False
                return
            
            credential = DefaultAzureCredential()
            self._client = SecretClient(vault_url=key_vault_url, credential=credential)
            self._initialized = True
            logger.info(f"Key Vault client initialized: {key_vault_url}")
            
        except ImportError:
            logger.warning(
                "Azure SDK not installed. Install with: pip install azure-identity azure-keyvault-secrets"
            )
            self.use_key_vault = False
        except Exception as e:
            logger.warning(
                f"Failed to initialize Key Vault client: {type(e).__name__}: {e}. "
                "Will use environment variables only."
            )
            self._initialization_error = e
            self.use_key_vault = False
    
    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Retrieve a secret from Key Vault or environment variables.
        
        Args:
            key: The secret name (e.g., 'POSTGRES-PASSWORD', 'SECRET-KEY')
            default: Default value if secret is not found
            
        Returns:
            The secret value, or default if not found and provided
            
        Raises:
            ValueError: If secret not found and no default provided
        """
        # Normalize key for Key Vault (replace underscores with hyphens)
        kv_key = key.replace("_", "-")
        
        # Try Key Vault first
        if self.use_key_vault and self._initialized:
            try:
                secret = self._client.get_secret(kv_key)
                logger.debug(f"Retrieved secret '{kv_key}' from Key Vault")
                return secret.value
            except Exception as e:
                logger.debug(
                    f"Secret '{kv_key}' not found in Key Vault: {type(e).__name__}"
                )
        
        # Fall back to environment variable
        env_value = os.getenv(key)
        if env_value:
            logger.debug(f"Retrieved secret '{key}' from environment variable")
            return env_value
        
        # Use default if provided
        if default is not None:
            logger.debug(f"Using default value for secret '{key}'")
            return default
        
        # Handle missing secret
        raise ValueError(
            f"Secret '{key}' not found in Key Vault or environment variables, "
            f"and no default value provided"
        )
    
    def get_optional(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Retrieve an optional secret (returns None if not found).
        
        Args:
            key: The secret name
            default: Default value if not found
            
        Returns:
            The secret value, default, or None
        """
        try:
            return self.get(key)
        except ValueError:
            return default
    
    def get_bool(self, key: str, default: bool = False) -> bool:
        """
        Retrieve a secret as a boolean.
        
        Args:
            key: The secret name
            default: Default boolean value if not found
            
        Returns:
            Boolean value (True if value is '1', 'true', 'yes', 'on', case-insensitive)
        """
        value = self.get_optional(key)
        if value is None:
            return default
        return value.lower() in ("1", "true", "yes", "on")
    
    def get_int(self, key: str, default: int = 0) -> int:
        """
        Retrieve a secret as an integer.
        
        Args:
            key: The secret name
            default: Default integer value if not found or invalid
            
        Returns:
            Integer value or default if conversion fails
        """
        value = self.get_optional(key)
        if value is None:
            return default
        try:
            return int(value)
        except ValueError:
            logger.warning(f"Failed to convert secret '{key}' to int, using default {default}")
            return default
    
    def get_list(self, key: str, delimiter: str = ",", default: Optional[list] = None) -> list:
        """
        Retrieve a secret as a list of values.
        
        Args:
            key: The secret name
            delimiter: Character to split values on (default: comma)
            default: Default list if not found
            
        Returns:
            List of values (stripped of whitespace)
        """
        value = self.get_optional(key)
        if value is None:
            return default if default is not None else []
        return [v.strip() for v in value.split(delimiter) if v.strip()]
    
    def get_all(self) -> Dict[str, Any]:
        """
        Get all secrets from Key Vault (if available).
        
        Note: This only works for Key Vault, not environment variables.
        Use with caution in logs or debugging.
        
        Returns:
            Dictionary of name: secret_value pairs from Key Vault
        """
        if not self.use_key_vault or not self._initialized:
            logger.warning("Key Vault not initialized; cannot retrieve all secrets")
            return {}
        
        try:
            secrets = {}
            for secret_property in self._client.list_properties_of_secrets():
                secret = self._client.get_secret(secret_property.name)
                secrets[secret_property.name] = secret.value
            return secrets
        except Exception as e:
            logger.error(f"Failed to retrieve all secrets from Key Vault: {e}")
            return {}
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check the health and configuration of the secrets manager.
        
        Returns:
            Dictionary with status, key vault URL, and any errors
        """
        vault_url = os.getenv("AZURE_KEY_VAULT_URL")
        return {
            "key_vault_enabled": self.use_key_vault,
            "key_vault_initialized": self._initialized,
            "key_vault_url": vault_url or "Not configured",
            "initialization_error": str(self._initialization_error) if self._initialization_error else None,
        }


# Global instance
_secrets_instance: Optional[SecretsManager] = None


def get_secrets_manager(use_key_vault: bool = True) -> SecretsManager:
    """
    Get the global secrets manager instance (singleton pattern).
    
    Args:
        use_key_vault: Whether to use Key Vault. Only applies on first call.
        
    Returns:
        SecretsManager instance
    """
    global _secrets_instance
    if _secrets_instance is None:
        _secrets_instance = SecretsManager(use_key_vault=use_key_vault)
    return _secrets_instance
