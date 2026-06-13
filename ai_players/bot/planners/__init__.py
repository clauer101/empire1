from .economy import EconomyPlanner
from .defense import DefensePlanner
from .attack import AttackPlanner
from .artifact import ArtifactPlanner

PLANNERS = {
    "economy": EconomyPlanner(),
    "defense": DefensePlanner(),
    "attack": AttackPlanner(),
    "artifact": ArtifactPlanner(prefer_artifacts=True),
}
