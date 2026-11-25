import pytest

from flowforge.phase5b.secrets import SecretReference, reject_raw_credentials


def test_reference():
    SecretReference("https://flowforge.vault.azure.net", "stripe-client-secret").validate()


def test_bad_uri():
    with pytest.raises(ValueError):
        SecretReference("http://x", "s").validate()


def test_raw_secret():
    with pytest.raises(ValueError):
        reject_raw_credentials({"client_secret": "x"})
