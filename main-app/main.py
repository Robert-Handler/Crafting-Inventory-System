
"""
Crafting System - Main Program (CLI Shell)
-----------------------------------------
Purpose:
  - Provide a user interface for the crafting system.
  - Communicate with multiple microservices (Auth, Inventory, Projects, etc.).
  - Maintain an auth token across requests after login.

How to run:
  python main.py

Config:
  You can override service URLs with environment variables:
    AUTH_URL=http://localhost:5000
    INVENTORY_URL=http://localhost:5001
    PROJECT_URL=http://localhost:5002

Requirements:
  pip install requests
"""

import os
import sys
import json
import getpass
from typing import Optional, Dict, Any

import requests


# ----------------------------
# Configuration & Environment
# ----------------------------

AUTH_URL = os.getenv("AUTH_URL", "http://localhost:5000")
INVENTORY_URL = os.getenv("INVENTORY_URL", "http://localhost:5001")
PROJECT_URL = os.getenv("PROJECT_URL", "http://localhost:5002")
