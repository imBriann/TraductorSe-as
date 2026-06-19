"""Arquitectura de Agentes i5.0 para el pipeline de interpretación LSC."""
from app.agents.base import Agent, AgentContext
from app.agents.context import ContextAgent
from app.agents.coordinator import CoordinatorAgent
from app.agents.perception import PerceptionAgent
from app.agents.persistence import PersistenceAgent
from app.agents.preprocessing import PreprocessingAgent
from app.agents.recognition import RecognitionAgent
from app.agents.semantic import SemanticAgent

__all__ = [
    "Agent",
    "AgentContext",
    "PerceptionAgent",
    "PreprocessingAgent",
    "RecognitionAgent",
    "ContextAgent",
    "SemanticAgent",
    "PersistenceAgent",
    "CoordinatorAgent",
]
