import os

# ISOLATE TESTS FROM DEVELOPMENT DATABASE
# Ensure all pytest runs use the dedicated test database instead of wiping development data
os.environ["DATABASE_NAME"] = "intellihire_test"
