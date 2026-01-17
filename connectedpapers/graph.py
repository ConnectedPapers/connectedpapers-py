"""
Graph data structures for Connected Papers API responses.

This module defines the dataclasses used to represent paper graphs returned by the API.
"""
import dataclasses
from typing import Any, Dict, List, Optional, Union

PaperID = str


@dataclasses.dataclass
class CommonAuthor:
    """An author who appears across multiple papers in the graph."""

    id: str
    mention_indexes: List[int]
    mentions: List[PaperID]
    name: str
    url: str


@dataclasses.dataclass
class PaperAuthor:
    """An author of a paper."""

    ids: List[Optional[str]]
    name: str


@dataclasses.dataclass
class ExternalIDs:
    """External identifiers for a paper from various academic databases."""

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
    """Base class containing common paper metadata fields."""

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
    """
    A derivative work - a paper that cites papers in the graph.

    These are typically newer papers that build upon the work in the graph.
    """

    edges_count: int
    local_references: List[PaperID]  # Papers in the graph that this paper references
    paper_id: PaperID
    pi_name: Optional[str]


@dataclasses.dataclass
class CommonReference(BasePaper):
    """
    A prior work - a paper that is cited by papers in the graph.

    These are typically older foundational papers that the graph papers build upon.
    """

    edges_count: int
    local_citations: List[PaperID]  # Papers in the graph that cite this paper
    paper_id: PaperID
    pi_name: Optional[str]


Edge = List[Union[PaperID, float]]  # [PaperID, PaperID, float] - similarity edge


@dataclasses.dataclass
class Paper(BasePaper):
    """A paper node in the similarity graph."""

    path: List[PaperID]  # Path from start paper to this paper
    path_length: float  # Distance from the start paper
    pos: List[float]  # [x, y] position in the graph visualization


@dataclasses.dataclass
class Graph:
    """
    The complete graph response from Connected Papers.

    Attributes:
        nodes: Papers in the similarity graph (the main visualization).
        edges: Similarity connections between papers in the graph.
        common_references: Prior works - foundational papers cited by papers in the graph.
        common_citations: Derivative works - newer papers that cite papers in the graph.
        common_authors: Authors appearing across multiple papers in the graph.
        start_id: The origin paper ID used to build this graph.
        path_lengths: Distance of each paper from the start paper.
    """

    common_authors: List[CommonAuthor]
    common_citations: List[CommonCitation]  # Derivative works
    common_references: List[CommonReference]  # Prior works
    edges: List[Edge]
    nodes: Dict[PaperID, Paper]
    path_lengths: Dict[PaperID, float]
    start_id: PaperID
