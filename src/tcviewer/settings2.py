def register_setting(category: str, variable_name: str, internal_name: str, limits: dict = None, defaults=None):
    # print(category, variable_name, internal_name, limits, defaults)
    def inner_dec(func):
        cls = func.__qualname__.split('.')[-2]
        if defaults is None:
            signature = inspect.signature(func)
            new_defaults = {k: v.default for k, v in signature.parameters.items() if v.default is not inspect._empty}
        else:
            new_defaults = defaults
        _registered_settings.append((category, variable_name, internal_name, limits, new_defaults, func, cls))
        return func
    return inner_dec
