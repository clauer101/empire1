from .defense import DefensePlanner
from .attack import AttackPlanner

PLANNERS = {
    "defense": DefensePlanner(),
    "attack":  AttackPlanner(),
}
