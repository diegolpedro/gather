import logging
import sys
import types

azure = types.ModuleType("azure")
core = types.ModuleType("azure.core")
exceptions = types.ModuleType("azure.core.exceptions")
exceptions.ResourceNotFoundError = type("ResourceNotFoundError", (Exception,), {})
core.exceptions = exceptions
azure.core = core

identity = types.ModuleType("azure.identity")
identity.ClientSecretCredential = type("ClientSecretCredential", (), {})

keyvault = types.ModuleType("azure.keyvault")
secrets_module = types.ModuleType("azure.keyvault.secrets")
secrets_module.SecretClient = type("SecretClient", (), {})
keyvault.secrets = secrets_module

storage = types.ModuleType("azure.storage")
blob_module = types.ModuleType("azure.storage.blob")
blob_module.BlobServiceClient = type(
    "BlobServiceClient",
    (),
    {"from_connection_string": staticmethod(lambda *args, **kwargs: None)},
)
storage.blob = blob_module

sys.modules.setdefault("azure", azure)
sys.modules.setdefault("azure.core", core)
sys.modules.setdefault("azure.core.exceptions", exceptions)
sys.modules.setdefault("azure.identity", identity)
sys.modules.setdefault("azure.keyvault", keyvault)
sys.modules.setdefault("azure.keyvault.secrets", secrets_module)
sys.modules.setdefault("azure.storage", storage)
sys.modules.setdefault("azure.storage.blob", blob_module)

from common.tools import Logger


def test_logger_separates_console_and_file_levels(tmp_path):
    log_file = tmp_path / "uphb.log"

    logger = Logger(
        "demo_logger",
        log_file=str(log_file),
        level=logging.DEBUG,
        console_level=logging.INFO,
        file_level=logging.DEBUG,
    ).get_logger()

    stream_handler = next(
        h
        for h in logger.handlers
        if isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)
    )
    file_handler = next(
        h for h in logger.handlers if isinstance(h, logging.FileHandler)
    )

    assert logger.level == logging.DEBUG
    assert stream_handler.level == logging.INFO
    assert file_handler.level == logging.DEBUG
