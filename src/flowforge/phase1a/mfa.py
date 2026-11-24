import hmac
from dataclasses import dataclass
from hashlib import sha256


@dataclass(slots=True)
class RecoveryCodes:
    hashes: set[str]

    @classmethod
    def from_plain(cls, codes: list[str]) -> "RecoveryCodes":
        return cls({sha256(c.encode()).hexdigest() for c in codes})

    def consume(self, code: str) -> bool:
        value = sha256(code.encode()).hexdigest()
        for saved in set(self.hashes):
            if hmac.compare_digest(saved, value):
                self.hashes.remove(saved)
                return True
        return False
