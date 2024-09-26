import inspect

from loguru import logger


def loguru_decorate(cls) -> 'cls':
    for attr in dir(cls):
        if not attr.startswith('__'):
            cur_attr = getattr(cls, attr)
            if inspect.isfunction(cur_attr):
                dec_attr = logger.catch(cur_attr)
                setattr(cls, attr, dec_attr)
    return cls