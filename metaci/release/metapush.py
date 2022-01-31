from typing import List

from pydantic import BaseModel

class DependencyGraphItem(BaseModel):
    AllPackageId: str  # 033
    AllPackageVersionId: str  # 04t
    Dependencies: List[str]  # List of 04ts


class DependencyGraph(BaseModel):
    __root__: List[DependencyGraphItem]

    def __iter__(self):
        return iter(self.__root__)
