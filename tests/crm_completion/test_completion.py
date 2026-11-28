import pytest
from pydantic import ValidationError

from flowforge.crm_completion.schemas import SearchRequest


def test_search_limit():
    with pytest.raises(ValidationError):
        SearchRequest(limit=201)
