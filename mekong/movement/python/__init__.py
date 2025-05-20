import os
import logging

__LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()

logging.basicConfig(
  level=__LOG_LEVEL,
  # format='[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s',
  format='[%(asctime)s] %(levelname)8s - %(message)s',
  handlers=[logging.FileHandler("example.log"), logging.StreamHandler()]
)

import warnings
warnings.filterwarnings("ignore", "Your application has authenticated using end user credentials")
