import random
from data.activity_dao import ActivityDAO

dao = ActivityDAO()


def get_weighted_random_valid_activity():
    """Return a random activity or subitem based on usage weights."""
    activities = dao.get_all_with_counts()
    if not activities:
        return None

    options = []  # (identifier, display_name, count)
    for act_id, name, count in activities:
        subitems = dao.get_subitems_by_activity(act_id)
        if subitems:
            for sub_id, _, sub_name, sub_count in subitems:
                options.append((f"s{sub_id}", f"{name} + {sub_name}", sub_count))
        else:
            options.append((f"a{act_id}", name, count))

    if not options:
        return None

    max_count = max(c for _, _, c in options) + 1
    weighted = []
    for identifier, display_name, count in options:
        weight = max_count - count
        weighted.extend([(identifier, display_name)] * weight)

    return random.choice(weighted) if weighted else None


def mark_item_as_done(identifier):
    """Increment usage count for an activity or subitem."""
    if isinstance(identifier, str) and identifier.startswith("s"):
        dao.increment_subitem_count(int(identifier[1:]))
    else:
        act_id = int(identifier[1:]) if isinstance(identifier, str) else identifier
        dao.increment_accepted_count(act_id)

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


def get_activity_weights():
    """Return all selectable items with weight and percentage."""
    activities = dao.get_all_with_counts()
    if not activities:
        return []

    options = []
    for act_id, name, count in activities:
        subitems = dao.get_subitems_by_activity(act_id)
        if subitems:
            for sub_id, _, sub_name, sub_count in subitems:
                options.append((f"s{sub_id}", f"{name} + {sub_name}", sub_count))
        else:
            options.append((f"a{act_id}", name, count))

    if not options:
        return []

    max_count = max(c for _, _, c in options) + 1
    weights = []
    total_weight = 0
    for identifier, name, count in options:
        weight = max_count - count
        weights.append((identifier, name, weight))
        total_weight += weight

    if total_weight == 0:
        return []

    return [
        (identifier, name, weight, (weight / total_weight) * 100)
        for identifier, name, weight in weights
    ]
