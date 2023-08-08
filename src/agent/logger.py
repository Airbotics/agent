import os
import logging

class AirLogger():

  LOG_FILE = os.path.join(os.path.expanduser("~"), "airbotics.log")
  
  def __init__(self, module, config) -> None:

    # Get a logger for the calling module
    self.logger = logging.getLogger(module)
    
    # Set the log format
    log_formatter = logging.Formatter('[%(levelname)s]: %(asctime)s - %(name)s - %(message)s')
    
    # Add the file handler
    log_file_handler = logging.FileHandler(os.path.join(os.getcwd(), self.LOG_FILE))
    log_file_handler.setFormatter(log_formatter)

    # Set the file handler
    self.logger.addHandler(log_file_handler)

    # Add a handler to log to the console when not daemonized
    if config['daemonize'] == False: 
      log_stream_handler = logging.StreamHandler()
      log_stream_handler.setFormatter(log_formatter)
      self.logger.addHandler(log_stream_handler)

    log_level = logging.DEBUG if config['debug'] else logging.INFO
    self.logger.setLevel(log_level)



