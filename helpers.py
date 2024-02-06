from typing import List, Dict, Optional, Tuple
from db import query_db


def get_image_sizes(
    images: List[Dict[str, any]]
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Sorts images by height and returns URLs for small, medium, and large images.
    """
    if not images:
        return None, None, None

    # Sort images by height
    sorted_images = sorted(images, key=lambda x: x["height"])

    # Assign URLs based on sorted order
    image_sm = sorted_images[0]["url"] if len(sorted_images) > 0 else None
    image_md = sorted_images[1]["url"] if len(sorted_images) > 1 else None
    image_lg = sorted_images[2]["url"] if len(sorted_images) > 2 else None

    return image_sm, image_md, image_lg


def startup_database() -> None:
    """
    Read database.sql and execute the queries.
    """
    with open("database.sql") as f:
        queries = f.read().split(";")

    # TODO: Do this without query_db function, write custom here
    for query in queries:
        if query.strip():
            query_db(query, commit=True)


def get_date_based_on_precision(precision: str, date: str) -> str:
    """
    Returns a date based on the precision.
    1994-01-01 -> 1994-01-01
    1994-01 -> 1994-01-01
    1994 -> 1994-01-01
    """
    if precision == "year":
        return f"{date}-01-01"
    elif precision == "month":
        return f"{date}-01"
    return date


def batch_generator(lst, n):
    """Yield successive n sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]
