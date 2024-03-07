from datetime import datetime
from pydantic import Field
from beanie import Document


class WikiData(Document):

    # id: PyObjectId = Field(alias="id")
    input: str
    output: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_occurrence: datetime = Field(default_factory=datetime.utcnow)
    is_deleted: bool = False
    search_count: int = 1

    def __str__(self) -> str:
        return f'{self.input}'
    