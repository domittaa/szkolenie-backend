"""Types shared by the API schemas."""

from datetime import datetime
from typing import Annotated

from pydantic import AfterValidator

from app.timeutils import as_utc

# Always serialized with a timezone, so that the frontend does not read UTC as local time
UtcDatetime = Annotated[datetime, AfterValidator(as_utc)]
