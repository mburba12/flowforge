import pytest
from pydantic import ValidationError
from flowforge.foundation_final.schemas import ArtifactClassify
def test_artifact_classification_bounded():
 with pytest.raises(ValidationError):ArtifactClassify(artifact_path='x',classification='invented')
