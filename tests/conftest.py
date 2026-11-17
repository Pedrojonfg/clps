import os

# Tests never touch the network: remote store off unless a test sets its own URL.
os.environ.setdefault("LUNAR_STORE_URL", "off")
