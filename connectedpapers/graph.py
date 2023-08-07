import dataclasses
from typing import Any, Dict, List, Optional, Union

PaperID = str


@dataclasses.dataclass
class CommonAuthor:
    id: str
    mention_indexes: List[int]
    mentions: List[PaperID]
    name: str
    url: str


@dataclasses.dataclass
class PaperAuthor:
    ids: List[Optional[str]]
    name: str


@dataclasses.dataclass
class ExternalIDs:
    ACL: Optional[str]
    ArXiv: Optional[str]
    CorpusId: Any
    DBLP: Optional[str]
    DOI: Optional[str]
    MAG: Optional[str]
    PubMed: Optional[str]
    PubMedCentral: Optional[str]


@dataclasses.dataclass
class BasePaper:
    abstract: Optional[str]
    arxivId: Optional[str]
    authors: List[PaperAuthor]
    corpusid: int
    doi: Optional[str]
    externalIds: ExternalIDs
    fieldsOfStudy: Optional[List[str]]
    id: PaperID
    isOpenAccess: Optional[bool]
    journalName: Optional[str]
    journalPages: Optional[str]
    journalVolume: Optional[str]
    magId: Optional[str]
    number_of_authors: int
    paperId: PaperID
    pdfUrls: Optional[List[str]]
    pmid: Optional[str]
    publicationDate: Optional[str]
    publicationTypes: Optional[List[str]]
    title: str
    tldr: Optional[str]
    url: str
    venue: Optional[str]
    year: Optional[int]


@dataclasses.dataclass
class CommonCitation(BasePaper):
    edges_count: int
    local_references: List[PaperID]
    paper_id: PaperID
    pi_name: Optional[str]


@dataclasses.dataclass
class CommonReference(BasePaper):
    edges_count: int
    local_citations: List[PaperID]
    paper_id: PaperID
    pi_name: Optional[str]


Edge = List[Union[PaperID, float]]  # [PaperID, PaperID, float]


@dataclasses.dataclass
class Paper(BasePaper):
    path: List[PaperID]
    path_length: float
    pos: List[float]  # [float, float]


@dataclasses.dataclass
class Graph:
    common_authors: List[CommonAuthor]
    common_citations: List[CommonCitation]
    common_references: List[CommonReference]
    edges: List[Edge]
    nodes: Dict[PaperID, Paper]
    path_lengths: Dict[PaperID, float]
    start_id: PaperID
