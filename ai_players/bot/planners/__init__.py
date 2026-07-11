from .defense_frontier import FrontierDefensePlanner
from .attack import AttackPlanner
from .growth import GrowthPlanner

PLANNERS = {
    "defense": FrontierDefensePlanner(),
    "attack":  AttackPlanner(),
    "growth":  GrowthPlanner(),
}
