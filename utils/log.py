def logger(level, info, verbose):
    if not verbose:
        return
    print("[%s] %s" % (level, info))
