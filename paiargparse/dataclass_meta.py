DEFAULT_SEPARATOR = '.'


def dc_meta(*,
            help=None,
            separator=DEFAULT_SEPARATOR,
            ):
    assert(separator in '/._-+')
    return locals()
