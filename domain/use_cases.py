import random
from data.activity_dao import ActivityDAO

dao = ActivityDAO()

def get_weighted_random_valid_activity():
    activities = dao.get_all_with_counts()
    if not activities:
        return None

    # Menor accepted_count => más peso
    max_count = max(a[2] for a in activities) + 1
    weighted = []
    for act in activities:
        hobby_id, name, count = act
        subitems = dao.get_subitems_by_activity(hobby_id)
        display_name = name
        if subitems:
            sub = random.choice(subitems)[2]
            display_name += f" + {sub}"
        weight = max_count - count
        weighted.extend([(hobby_id, display_name)] * weight)

    return random.choice(weighted) if weighted else None

def mark_activity_as_done(activity_id):
    dao.increment_accepted_count(activity_id)

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
    """Return activities with their calculated weights and percentages."""
    activities = dao.get_all_with_counts()
    if not activities:
        return []

    max_count = max(a[2] for a in activities) + 1
    weights = []
    total_weight = 0
    for hobby_id, name, count in activities:
        weight = max_count - count
        weights.append((hobby_id, name, weight))
        total_weight += weight

    if total_weight == 0:
        return []

    return [
        (hobby_id, name, weight, (weight / total_weight) * 100)
        for hobby_id, name, weight in weights
    ]
