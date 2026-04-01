import logging

NO_LOGGER = logging.getLogger("NO_LOGGER")
NO_LOGGER.addHandler(logging.NullHandler())
NO_LOGGER.setLevel(logging.CRITICAL)
