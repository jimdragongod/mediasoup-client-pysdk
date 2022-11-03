import logging


class Logger:
    @staticmethod
    def getLogger(enable_console, log_file_path, level):
        logger = logging.getLogger()
        logger.setLevel(level)
        # 日志格式
        formatter = logging.Formatter(
            "%(asctime)s -$- [%(threadName)s] -$- %(levelname)s -$- %(filename)s -$- %(funcName)s(%(lineno)d) -$- %(message)s")

        if enable_console:
            # 建立一个stream handler来把日志打在CMD窗口上，级别为error以上
            console_handler = logging.StreamHandler()
            console_handler.setLevel(level)
            console_handler.setFormatter(formatter)
            # 将相应的handler添加在logger对象中
            logger.addHandler(console_handler)

        if log_file_path is not None:
            # 建立一个filehandler来把日志记录在文件里，级别为debug以上
            file_handler = logging.FileHandler(log_file_path)
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        return logger
