from App.models import Resident, Stop, Drive, Area, Street, DriverStock
from App.database import db



# RESIDENT ACCOUNT MANAGEMENT


def resident_create(username, password, areaId, streetId, houseNumber):
    resident = Resident(
        username=username,
        password=password,
        areaId=areaId,
        streetId=streetId,
        houseNumber=houseNumber
    )
    db.session.add(resident)
    db.session.commit()
    return resident



# DRIVE SUBSCRIPTIONS


def resident_subscribe_to_drive(resident, drive_id):
    drive = Drive.query.get(drive_id)

    if not drive:
        raise ValueError("Drive not found.")

    if drive.areaId != resident.areaId or drive.streetId != resident.streetId:
        raise ValueError("Cannot subscribe to drives outside your area and street.")

    resident.subscribe_to_drive(drive_id)
    return True


def resident_unsubscribe_from_drive(resident, drive_id):
    resident.unsubscribe_from_drive(drive_id)
    return True


def resident_get_subscribed_drives(resident):
    return Drive.query.filter(Drive.id.in_(resident.subscribed_drives)).all()



# STOP REQUESTS


def resident_request_stop(resident, drive_id):
    # Check the drive exists AND is upcoming AND in the correct location
    drive = Drive.query.get(drive_id)
    if not drive:
        raise ValueError("Drive not found.")

    if drive.status != "Upcoming":
        raise ValueError("Cannot request stops for drives that have started or ended.")

    if drive.areaId != resident.areaId or drive.streetId != resident.streetId:
        raise ValueError("Invalid drive choice: Not your area/street.")

    # Check if stop already exists
    existing_stop = Stop.query.filter_by(
        driveId=drive_id, residentId=resident.id
    ).first()

    if existing_stop:
        raise ValueError(f"You have already requested a stop for drive {drive_id}.")

    stop =  resident.request_stop(drive_id)

    resident.receive_notif(
        f"Your stop request for Drive {drive_id} was submitted.",
        "stop_requested",
        drive_id
    )

    return stop


def resident_request_stop_from_notification(resident, drive_id):
    """Request a stop after receiving a notification."""
    return resident_request_stop(resident, drive_id)


def resident_cancel_stop(resident, drive_id):
    stop = Stop.query.filter_by(
        driveId=drive_id, residentId=resident.id
    ).first()

    if not stop:
        raise ValueError("No stop requested for this drive.")

    resident.cancel_stop(stop.id)
    return stop



# NOTIFICATIONS


def resident_view_inbox(resident):
    return resident.view_inbox()


def resident_get_notifications(resident, unread_only=False):
    return resident.view_inbox(unread_only=unread_only)


def resident_get_notification_stats(resident):
    inbox = resident.view_inbox()
    unread_count = resident.get_unread_count()

    return {
        "total_notifications": len(inbox),
        "unread_notifications": unread_count,
        "notification_preferences": getattr(resident, "notification_preferences", [])
    }


def resident_mark_notification_read(resident, notification_index):
    resident.mark_notification_read(notification_index)
    return True


def resident_mark_all_notifications_read(resident):
    resident.mark_all_notifications_read()
    return True


def resident_clear_notifications(resident):
    resident.clear_inbox()
    return True


def resident_update_notification_preferences(resident, preferences):
    resident.update_notification_preferences(preferences)
    db.session.commit()
    return resident



# DRIVER INFORMATION VIEWS


def resident_view_driver_stats(resident, driver_id):
    driver = resident.view_driver_stats(driver_id)

    if not driver:
        raise ValueError("Driver not found.")

    return driver


def resident_view_stock(resident, driver_id):
    # Validate driver first
    driver = resident.view_driver_stats(driver_id)
    if not driver:
        raise ValueError("Driver not found.")

    stocks = DriverStock.query.filter_by(driverId=driver_id).all()
    return stocks
