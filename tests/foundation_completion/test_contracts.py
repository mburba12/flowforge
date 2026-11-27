import pytest
from pydantic import ValidationError

from flowforge.foundation_completion.schemas import StewardshipCreate


def test_priority_bounds():
    with pytest.raises(ValidationError):
        StewardshipCreate(task_type="review", priority=9)
