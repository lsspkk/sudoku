#!/usr/bin/env python
import sys
import os
import logging
import traceback

# Setup basic logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("test_environment")

def main():
    try:
        logger.info("Testing Python environment...")
        logger.info(f"Python version: {sys.version}")
        logger.info(f"Current working directory: {os.getcwd()}")
        
        # Test directory access and creation
        logger.info("Testing directory access...")
        test_dir = "test_dir"
        if not os.path.exists(test_dir):
            os.makedirs(test_dir)
            logger.info(f"Created test directory: {test_dir}")
        else:
            logger.info(f"Test directory already exists: {test_dir}")
        
        # Test file read/write
        logger.info("Testing file read/write...")
        test_file = os.path.join(test_dir, "test_file.txt")
        with open(test_file, "w") as f:
            f.write("Hello, world!")
        logger.info(f"Created test file: {test_file}")
        
        with open(test_file, "r") as f:
            content = f.read()
        logger.info(f"Read test file content: {content}")
        
        # Clean up
        os.remove(test_file)
        os.rmdir(test_dir)
        logger.info("Cleaned up test directory and file")
        
        # List available modules
        logger.info("Available modules:")
        import pkg_resources
        for d in pkg_resources.working_set:
            logger.info(f"  {d.project_name} ({d.version})")
        
        logger.info("Environment test completed successfully")
        return 0
    
    except Exception as e:
        logger.error(f"Error: {e}")
        logger.error(traceback.format_exc())
        return 1

if __name__ == "__main__":
    sys.exit(main()) 