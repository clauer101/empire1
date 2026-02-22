---
name: Empire
description: Implement HTML/JS/CSS and Python Games
argument-hint: Implementation task, Planning task
model: Claude Sonnet 4.6 (agent), Claude Opus 4.6 (agent)
# tools: ['vscode', 'execute', 'read', 'agent', 'edit', 'search', 'web', 'todo'] # specify the tools this agent can use. If not set, all enabled tools are allowed.
---


## Repo Structure
The goal of this agent is to implement the same game in HTML/JS/CSS and Python. The game is a turn-based strategy game where players control planets and fleets to conquer the galaxy.

Repo structure:
/home/pi/e3/java_implementation
This Folder container the old implementation in Java. Ignore this folder unless told otherwise.

/home/pi/e3/web
This folder should contain the HTML/JS/CSS implementation of the game. The main entry point should be index.html. The game should be playable in a web browser and mobile browsers.

/home/pi/e3/web/js/views
This folder should contain the JS files for the different views of the game. For example, there should be a file for the main menu, the army view, the settings view, etc.

/home/pi/e3/web/assets/sprites
This folder should contain the sprite sheets for the game. The main sprite sheet is map.webp, which contains all the sprites for the game. 

/home/pi/e3/python_server/src/gameserver/engine
This folder should contain the Python implementation of the game logic.

/home/pi/e3/python_server/src/gameserver/models
This is the folder for the data models of the game. 

/home/pi/e3/python_server/src/gameserver/engine/battle_service.py
Main file for the battle logic of the game. This file should contain the implementation of the battle mechanics, such as how critters move, towers shoot, how damage is calculated, etc.

/home/pi/e3/web/tools
This folder should contain the tools for the web implementation. For example, a sprite inspector.

/home/pi/e3/python_server/src/gameserver/models/hex.py
This file contains the implementation of the hexagonal grid used in the game. It should contain the data model for the hexagonal grid, as well as the logic for calculating distances, neighbors, etc.

## Changes a the data models
Every time the data models change also the serialization and deserialization logic has to be updated.
Relevant entrypoint: /home/pi/e3/python_server/src/gameserver/persistence/state_load.py

## Changes in the data exchange between client and server
When the data exchange between client and server changes, the API endpoints have to be updated. 
Relevant entrypoints: 
* /home/pi/e3/python_server/src/gameserver/api/endpoints.py
* /home/pi/e3/web/js/api.js
* /home/pi/e3/python_server/src/gameserver/network/handlers.py

## Venv used inb this project
The project uses a venv located at /home/pi/e3/.venv. To activate the venv, run `source /home/pi/e3/.venv/bin/activate`.

## Running all tests
To run all tests use
´´´bash
cd /home/pi/e3/python_server && PYTHONPATH=src /home/pi/e3/.venv/bin/python -m pytest tests/ -q --tb=short 2>&1 | tail -20
´´´