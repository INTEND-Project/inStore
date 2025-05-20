from pkg.config import KnowledgeGraphInfo, KnowledgeGraphType, Neo4jKnowledgeGraphConfig
from pkg.interfaces import KnowledgeGraph

from .kg_n4j import Neo4jKnowledgeGraph


def knowledge_graph_factory(info: KnowledgeGraphInfo) -> KnowledgeGraph:
    if info.provider == KnowledgeGraphType.NEO4J.value:
        neo4j_cfg = Neo4jKnowledgeGraphConfig(cfg=info.config)
        return Neo4jKnowledgeGraph(cfg=neo4j_cfg)
    raise ValueError(f"Unknown intent db type {info.provider}")
