import random
from data.activity_dao import ActivityDAO

dao = ActivityDAO()


def _build_weighted_items():
    """Return hobby items alongside their selection weights."""
    activities = dao.get_all_with_counts()
    if not activities:
        return [], []

    temp_items = []
    for hobby_id, name, act_count in activities:
        subitems = dao.get_subitems_by_activity(hobby_id)
        if subitems:
            for sub_id, _, sub_name, sub_count in subitems:
                temp_items.append((sub_id, f"{name} + {sub_name}", True, sub_count))
        else:
            temp_items.append((hobby_id, name, False, act_count))

    max_count = max(item[3] for item in temp_items) + 1
    items: list[tuple[int, str, bool]] = []
    weights: list[int] = []
    for item_id, label, is_sub, count in temp_items:
        weight = max_count - count
        items.append((item_id, label, is_sub))
        weights.append(weight)
    return items, weights


def get_weighted_random_valid_activity():
    items, weights = _build_weighted_items()
    if not items:
        return None
    return random.choices(items, weights=weights, k=1)[0]

def mark_activity_as_done(item_id, is_subitem):
    if is_subitem:
        dao.increment_subitem_accepted_count(item_id)
    else:
        dao.increment_accepted_count(item_id)

def create_hobby(name):
    return dao.insert_activity(name)

def add_subitem_to_hobby(hobby_id, item_name):
    dao.insert_subitem(hobby_id, item_name)

def get_all_hobbies():
    return dao.get_all_activities()

def get_subitems_for_hobby(hobby_id):
    return dao.get_subitems_by_activity(hobby_id)

def delete_subitem(subitem_id):
    dao.delete_subitem(subitem_id)

def delete_hobby(hobby_id):
    dao.delete_activity(hobby_id)

def update_subitem(subitem_id, new_name):
    dao.update_subitem(subitem_id, new_name)


def get_activity_probabilities():
    items, weights = _build_weighted_items()
    if not items:
        return []

    total_weight = sum(weights)
    return [
        (label, weight / total_weight)
        for (_, label, _), weight in zip(items, weights)
    ]

