import logging


class Logger:
    @staticmethod
    def getLogger(module_name: str, level=logging.WARNING, enable_console=True, log_file_path=None):
        """
        This logger factory method is only for internal use.
        e.g.
        logger = Logger.getLogger(__name__,level=logging.DEBUG,log_file_path='D:/logs/1/smcdk.log')
        :param module_name:
        :param level:
        :param enable_console:
        :param log_file_path:
        :return:
        """
        logger = logging.getLogger(module_name)
        logger.setLevel(level)
        # set logger format
        formatter = logging.Formatter(
            "%(asctime)s -$- [%(threadName)s] -$- %(levelname)s -$- %(filename)s -$- %(funcName)s(%(lineno)d) -$- %(message)s")

        if enable_console:
            # console logger
            console_handler = logging.StreamHandler()
            console_handler.setLevel(level)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

        if log_file_path is not None:
            # file logger
            file_handler = logging.FileHandler(log_file_path)
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        return logger
