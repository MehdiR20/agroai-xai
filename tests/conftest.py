import sys
from pathlib import Path

# Make the project root importable (api_services, translations).
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
