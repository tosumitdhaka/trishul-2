# lazy import — do not instantiate at module level
def get_plugin():
    from plugins.snmp.plugin import plugin
    return plugin
