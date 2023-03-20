import logging
import inspect
logger = logging.getLogger("apps")


def log_entry(*args):
    stack = inspect.stack()
    try:
        logger.debug(f" LOG_ENTRY  filename: {stack[1].filename} lineno: {stack[1].lineno} method: {stack[1].function} parmas: {args}")
    except Exception as e:
        print(f"exception: Stack Frame {str(e)}")


def log_exit(*args):
    stack = inspect.stack()
    try:
        logger.debug(f" LOG_EXIT  filename: {stack[1].filename} lineno: {stack[1].lineno} method: {stack[1].function} parmas: {args}")
    except Exception as e:
        print(f"exception: Stack Frame {str(e)}")


def log_error(*args):
    stack = inspect.stack()
    try:
        logger.debug(f" LOG_ERROR args: {args} #### {stack[1].frame.f_locals} lineno: {stack[1].lineno}")
    except Exception as e:
        print(f"exception: Stack Frame {str(e)}")
