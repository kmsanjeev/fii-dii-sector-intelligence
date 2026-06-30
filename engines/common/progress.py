from tqdm import tqdm


def progress(iterable, total=None, desc="Processing"):
    return tqdm(
        iterable,
        total=total,
        desc=desc,
        ncols=100,
        leave=True,
        ascii=True,       # Windows cp1252 safe -- no Unicode bar chars
    )