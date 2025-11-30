from App.models import Stop, Drive, Resident
from App.database import db

# All stop-related business logic will be moved here as functions
def create_stop(drive_id, resident_id):
    stop = Stop(driveId=drive_id, residentId=resident_id)
    db.session.add(stop)
    db.session.commit()
    return stop


def get_stops_by_drive(drive_id):
    return Stop.query.filter_by(driveId=drive_id).all() 


def get_stops_by_resident(resident_id):
    return Stop.query.filter_by(residentId=resident_id).all()


def delete_stop(stop_id):
    stop = Stop.query.get(stop_id)
    if not stop:
        raise ValueError("Invalid stop ID.")
    db.session.delete(stop)
    db.session.commit()
    return stop


def get_all_stops():
    return Stop.query.all() 



def get_stops_by_drive_and_resident(drive_id, resident_id):
    return Stop.query.filter_by(driveId=drive_id, residentId=resident_id).all()