"""Lets the tests import the project's backend code (backend/modules, app.py)."""
import os
import sys
 
BACKEND = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
 
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)
 

