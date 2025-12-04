from App.models import Street, Area
from App.database import db

# All street-related business logic will be moved here as functions
def create_street(areaId, name):
    area = Area.query.get(areaId)
    if not area:
        raise ValueError("Invalid area ID.")
    street = Street(name=name, areaId=areaId)
    db.session.add(street)
    db.session.commit()
    return street


def get_street_by_id(areaId, street_id):
    area = Area.query.get(areaId)
    if not area:
        raise ValueError("Invalid area ID.")
    street = Street.query.filter_by(areaId=areaId).get(street_id)
    if not street:
        raise ValueError("Invalid street ID.")
    return street

def get_all_streets():
    return Street.query.all()

def delete_street(areaId, street_id):
    area = Area.query.get(areaId)
    if not area:
        raise ValueError("Invalid area ID.")
    street = Street.query.filter_by(areaId=areaId).get(street_id)
    if not street:
        raise ValueError("Invalid street ID.")
    db.session.delete(street)
    db.session.commit()



def get_streets_by_name(name):
    return Street.query.filter(Street.name.ilike(f"%{name}%")).all()

def get_streets_by_area(area_id):
    return Street.query.filter_by(areaId=area_id).all()

