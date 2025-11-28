from App.models import Area, Street
from App.database import db

# All area-related business logic will be moved here as functions
def create_area(name):
    area = Area(name=name)
    db.session.add(area)
    db.session.commit()
    return area


def get_area_by_id(area_id):
    area = Area.query.get(area_id)
    if not area:
        raise ValueError("Invalid area ID.")
    return area

def get_streets_in_area(area_id):
    area = Area.query.get(area_id)
    if not area:
        raise ValueError("Invalid area ID.")
    return Street.query.filter_by(areaId=area_id).all()

def get_all_areas():
    return Area.query.all()


def delete_area(area_id):
    area = Area.query.get(area_id)
    if not area:
        raise ValueError("Invalid area ID.")
    db.session.delete(area)
    db.session.commit()