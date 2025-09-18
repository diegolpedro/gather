"""Configuration helpers for the alerts service."""
from __future__ import annotations

import os
from functools import lru_cache
from typing import Optional

from azure.identity import ClientSecretCredential
from azure.keyvault.secrets import SecretClient


class ConfigurationError(RuntimeError):
    """Raised when required configuration values are missing or invalid."""


def _get_env(name: str, *, default: Optional[str] = None) -> str:
    """Retrieve an environment variable with validation."""
    value = os.getenv(name, default)
    if value is None or value == "":
        raise ConfigurationError(f"Environment variable '{name}' is required")
    return value


@lru_cache
def get_secret_client() -> SecretClient:
    """Return a cached instance of :class:`~azure.keyvault.secrets.SecretClient`."""

    tenant_id = _get_env("AZURE_TENANT_ID")
    client_id = _get_env("AZURE_CLIENT_ID")
    client_secret = _get_env("AZURE_CLIENT_SECRET")
    vault_url = _get_env("AZURE_VAULT_URL")

    credential = ClientSecretCredential(
        tenant_id=tenant_id,
        client_id=client_id,
        client_secret=client_secret,
    )
    return SecretClient(vault_url=vault_url, credential=credential)


def _get_secret(name_env_var: str) -> str:
    secret_name = _get_env(name_env_var)
    secret = get_secret_client().get_secret(secret_name)
    return secret.value


@lru_cache
def get_telegram_token() -> str:
    return _get_secret("ALERTS_TELEGRAM_TOKEN_SECRET_NAME")


@lru_cache
def get_smtp_username() -> str:
    return _get_secret("ALERTS_SMTP_USERNAME_SECRET_NAME")


@lru_cache
def get_smtp_password() -> str:
    return _get_secret("ALERTS_SMTP_PASSWORD_SECRET_NAME")


@lru_cache
def get_email_sender() -> str:
    return _get_secret("ALERTS_EMAIL_FROM_SECRET_NAME")


def get_smtp_host() -> str:
    return _get_env("ALERTS_SMTP_HOST")


def get_smtp_port() -> int:
    value = _get_env("ALERTS_SMTP_PORT")
    try:
        return int(value)
    except ValueError as exc:
        raise ConfigurationError("ALERTS_SMTP_PORT must be an integer") from exc


def get_smtp_use_tls() -> bool:
    value = _get_env("ALERTS_SMTP_USE_TLS")
    return value.strip().lower() in {"1", "true", "yes", "on"}


@lru_cache
def get_database_url() -> str:
    """Return the SQLAlchemy database URL for persisting alert logs."""

    secret_name = os.getenv("ALERTS_DATABASE_URL_SECRET_NAME")
    if secret_name:
        secret_value = get_secret_client().get_secret(secret_name).value
        if not secret_value:
            raise ConfigurationError(
                "Secret referenced by ALERTS_DATABASE_URL_SECRET_NAME is empty"
            )
        return secret_value

    return _get_env("ALERTS_DATABASE_URL")


__all__ = [
    "ConfigurationError",
    "get_secret_client",
    "get_telegram_token",
    "get_smtp_username",
    "get_smtp_password",
    "get_email_sender",
    "get_smtp_host",
    "get_smtp_port",
    "get_smtp_use_tls",
    "get_database_url",
]
