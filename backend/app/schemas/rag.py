from pydantic import BaseModel


class QueryRequest(BaseModel):

    question: str


class Source(BaseModel):

    text: str


class QueryResponse(BaseModel):

    answer: str

    sources: list[Source]