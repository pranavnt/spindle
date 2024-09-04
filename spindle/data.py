from dataclasses import dataclass, field
from collections import defaultdict
from typing import List, Dict, Any
import hashlib

@dataclass
class Document:
    title: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    id: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = hashlib.sha256((self.title +"::" + self.content).encode()).hexdigest()

@dataclass
class Link:
    target: str
    metadata: Dict[str, Any] = field(default_factory=dict)

class Wiki:
    docs: Dict[str, Document] = field(default_factory=dict)
    links: Dict[str, List[Link]] = field(default_factory=lambda: defaultdict(list))
    backlinks: Dict[str, List[Link]] = field(default_factory=lambda: defaultdict(list))

    def __init__(self):
        self.docs = {}
        self.links = defaultdict(list)
        self.backlinks = defaultdict(list)

    def add(self, title: str, content: str, metadata: Dict[str, Any] = {}) -> str:
        doc = Document(id="", title=title, content=content, metadata=metadata or {})
        self.docs[doc.id] = doc
        return doc.id

    def add_link(self, src: Document, tgt: Document, metadata: Dict[str, Any] = {}) -> None:
        self.links[src.id].append(Link(target=tgt.id, metadata=metadata or {}))
        self.backlinks[tgt.id].append(Link(target=src.id, metadata=metadata or {}))

@dataclass
class Node:
    title: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.id:
            self.id = hashlib.sha256((self.title +"::" + self.content).encode()).hexdigest()

class Graph:
    def __init__(self):
        self.nodes = {}
        self.edges = defaultdict(list)

    def create(self, title: str, content: str, metadata: Dict[str, Any] = {}) -> str:
        node = Node(title=title, content=content, metadata=metadata or {})
        self.nodes[node.id] = node
        if node.id not in self.edges:
            self.edges[node.id] = []
        return node.id

    def add_node(self, node: Node):
        self.nodes[node.id] = node
        if node.id not in self.edges:
            self.edges[node.id] = []

    def add_edge(self, src: Node, tgt: Node, metadata: Dict[str, Any] = {}) -> None:
        self.edges[src.id].append(Link(target=tgt.id, metadata=metadata or {}))
        self.edges[tgt.id].append(Link(target=src.id, metadata=metadata or {})
