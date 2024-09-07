from pydantic import BaseModel, Field, NonNegativeInt
from typing import List, Optional

# note that openai structured_result does NOT support "examples" field specification
# note that openai structured_result does NOT support "miniumum or maximum" field specification (or "gt" or "lt")
# note that the descriptions ARE useful to guide the AI extraction!! (see writein field for example)
class Choice(BaseModel):
    "Describes a choice in a contest"
    name: str
    party: Optional[str] = None
    writein: bool = Field(description="True only if this choice is a write-in as indicated by a '(w)' after the name")
    vote_in_center: int = Field(..., description="The number of votes for this choice in the voting center.")
    vote_by_mail: int = Field(..., description="The number of votes for this choice that were vote by mail")
    vote_total: int = Field(..., description="The total number of votes for this choice")


class Contest(BaseModel):
    "Describes a contest in an election"
    name: str = Field(..., 
        description="""
            The name of the contest, will be in upper case, followed optionally by the party.
            The instruction "vote for xxx" is NOT part of the contest name. For example, 
            'PRESIDENT - Demogcratic', 'US SENATOR - Republican', 'US REPRESENTATIVE - District 1', 'STATE SENATOR - District 1'
            """)
    choices: List[Choice]


class Summary(BaseModel):
    "Describes the summary of over and under votes and write-ins for an election"
    contest: str
    undervotes_in_center: int
    undervotes_by_mail: int
    overvotes_in_center: int
    overvotes_by_mail: int
    undervotes_total: int
    overvotes_total: int
    unqualified_write_ins_in_center: int
    unqualified_write_ins_by_mail: int
    unqualified_write_ins_total: int

class ElectionData(BaseModel):
    "Describes the data extracted from an election PDF"
    contests: List[Contest]
    summary: List[Summary]

