from App.models import Drive, Street, Area
from App.database import db

# All drive-related business logic will be moved here as functions

def add_drive(new_drive):
    db.session.add(new_drive)
    db.session.commit()
    return new_drive


def get_drives_by_area_and_street(area_id, street_id):
    return Drive.query.filter_by(areaId=area_id, streetId=street_id).all()

def get_upcoming_drives():
    return Drive.query.filter_by(status="Upcoming").all()

def delete_drive(drive_id):
    drive = Drive.query.get(drive_id)
    if not drive:
        raise ValueError("Invalid drive ID.")
    db.session.delete(drive)
    db.session.commit()
    return drive

def get_drives_by_driver(driver_id):
    return Drive.query.filter_by(driverId=driver_id).all()


def get_drives_by_status(status):
    return Drive.query.filter_by(status=status).all()


def get_drives_scheduled_between(start_date, end_date):
    return Drive.query.filter(Drive.scheduledTime >= start_date, Drive.scheduledTime <= end_date).all()


def get_all_drives():
    return Drive.query.all()

def get_drives_by_area(area_id):
    return Drive.query.filter_by(areaId=area_id).all()


def get_drives_by_street(street_id):
    return Drive.query.filter_by(streetId=street_id).all()

def get_drives_by_date(date):
    return Drive.query.filter(db.func.date(Drive.scheduledTime) == date).all()

