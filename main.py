"""Main application entrypoint for Restaurant Ordering and Billing Management System."""
import sys
import os
import logging
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Configure application logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("RestaurantPOS")


def main():
    logger.info("Starting Restaurant Ordering and Billing Management System...")
    try:
        from ui.app import RestaurantPOSApp
        app = RestaurantPOSApp()
        app.mainloop()
    except Exception as e:
        logger.critical(f"Fatal error running application: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
