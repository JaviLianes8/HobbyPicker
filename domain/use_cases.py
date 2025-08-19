import random
from data.activity_dao import ActivityDAO

dao = ActivityDAO()

def get_weighted_random_valid_activity():
    activities = dao.get_all_with_counts()
    if not activities:
        return None

    items = []
    for hobby_id, name, act_count in activities:
        subitems = dao.get_subitems_by_activity(hobby_id)
        if subitems:
            for sub_id, _, sub_name, sub_count in subitems:
                items.append((True, sub_id, f"{name} + {sub_name}", sub_count))
        else:
            items.append((False, hobby_id, name, act_count))

    max_count = max(i[3] for i in items) + 1
    weighted = []
    for is_sub, item_id, label, count in items:
        weight = max_count - count
        weighted.extend([(item_id, label, is_sub)] * weight)

    return random.choice(weighted) if weighted else None

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
    activities = dao.get_all_with_counts()
    if not activities:
        return []

    items = []
    for hobby_id, name, act_count in activities:
        subitems = dao.get_subitems_by_activity(hobby_id)
        if subitems:
            for sub_id, _, sub_name, sub_count in subitems:
                items.append((f"{name} + {sub_name}", sub_count))
        else:
            items.append((name, act_count))

    max_count = max(cnt for _, cnt in items) + 1
    weighted = []
    for label, count in items:
        weighted.append((label, max_count - count))

    total_weight = sum(w for _, w in weighted)
    return [(label, w / total_weight) for label, w in weighted]

