# Game Effects Reference

Comprehensive list of all available effects that can be granted by buildings and knowledge items.

## Passive Effects

| Effect Key | Description | Type | Example |
|---|---|---|---|
| `gold_offset` | Flat gold income per second (constant) | Economic | Fire Place: +0.1 gold/sec |
| `gold_modifier` | Multiplier on base gold income (percentage) | Economic | Exchange Post: +10% base gold |
| `culture_offset` | Flat culture income per second (constant) | Cultural | Stone Circle: +0.1 culture/sec |
| `culture_modifier` | Multiplier on base culture income (percentage) | Cultural | Epic Drawings: +10% base culture |
| `life_offset` | Health restoration per second (constant) | Medical | Medicus: +0.01 health/sec |
| `build_speed_modifier` | Multiplier on construction speed (percentage) | Manufacturing | Tool Shop: +10% build speed |
| `research_speed_modifier` | Multiplier on research speed (percentage) | Scientific | Library: +15% research speed |

## Usage

Build or research an item to gain its effects permanently. Effects stack across multiple completed items.

### Examples

- **FIRE_PLACE** grants `gold_offset: 0.1` → +0.1 gold/sec
- **TOOL_SHOP** grants `build_speed_modifier: 0.1` → +10% faster building
- **LIBRARY** grants `research_speed_modifier: 0.15` → +15% faster research
- **MEDICUS** grants `life_offset: 0.01` → +0.01 health/sec

## Stacking

When multiple items grant the same effect, values are summed:
- Two items with `gold_offset: 0.1` = total `gold_offset: 0.2`
- One item with `gold_modifier: 0.1` + one with `gold_modifier: 0.2` = total `gold_modifier: 0.3`
