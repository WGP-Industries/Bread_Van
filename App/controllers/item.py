from App.models import  Driver, Area, Street, Item
from App.database import db


def add_item(name, price, description, tags):
    item = Item(name=name, price=price, description=description, tags=tags)
    db.session.add(item)
    db.session.commit()
    return item

def get_item_by_id(item_id):
    item = Item.query.get(item_id)
    if not item:
        raise ValueError("Invalid item ID.")
    return item


def get_all_items():   
    return Item.query.all()


def delete_item(item_id):
    item = Item.query.get(item_id)
    if not item:
        raise ValueError("Invalid item ID.")
    db.session.delete(item)
    db.session.commit()


def get_items_by_name(name):
    return Item.query.filter(Item.name.ilike(f"%{name}%")).all()

def get_items_by_tag(tag):
    return Item.query.filter(Item.tags.ilike(f"%{tag}%")).all()

def update_item(item_id, name=None, price=None, description=None, tags=None):
    item = Item.query.get(item_id)
    if not item:
        raise ValueError("Invalid item ID.")
    if name is not None:
        item.name = name
    if price is not None:
        item.price = price
    if description is not None:
        item.description = description
    if tags is not None:
        item.tags = tags
    db.session.commit()
    return item




