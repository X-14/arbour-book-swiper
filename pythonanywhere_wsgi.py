import sys
import os

# ⚠️ REPLACE 'yourusername' WITH YOUR ACTUAL PYTHONANYWHERE USERNAME
# Example: If your username is 'john', replace all 4 instances of 'yourusername' with 'john'

# Add your project directory to the sys.path
project_home = '/home/yourusername/arbour_book_swiper'
if project_home not in sys.path:
    sys.path = [project_home] + sys.path

# Set environment variables
os.environ['PYTHONPATH'] = project_home

# Activate virtual environment
activate_this = '/home/yourusername/arbour_book_swiper/venv/bin/activate_this.py'
if os.path.exists(activate_this):
    with open(activate_this) as file_:
        exec(file_.read(), dict(__file__=activate_this))

# Import your Flask app
# The 'app' variable in app.py becomes 'application' for WSGI
from app import app as application

# Optional: Set up logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info('Flask app loaded successfully')
