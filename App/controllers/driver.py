from App.models import Driver, Drive, Street, Item, DriverStock, Resident
from App.database import db
from datetime import datetime, timedelta
from math import radians, sin, cos, sqrt, atan2

# DRIVER ACCOUNT MANAGEMENT


def create_driver(username, password, status="Offline", areaId=0, streetId=None):
    existing_user = Driver.query.filter_by(username=username).first()
    if existing_user:
        raise ValueError("Username already taken.")

    driver = Driver(
        username=username,
        password=password,
        status=status,
        areaId=areaId,
        streetId=streetId
    )

    db.session.add(driver)
    db.session.commit()

    return driver


def delete_driver(driver_id):
    driver = Driver.query.get(driver_id)
    if not driver:
        raise ValueError("Invalid driver ID.")

    db.session.delete(driver)
    db.session.commit()

    return driver



# DRIVER DRIVE MANAGEMENT


def driver_schedule_drive(driver, area_id, street_id, date_str, time_str, menu=None, eta_str=None):
    # Validate date + time formats
    try:
        date = datetime.strptime(date_str, "%Y-%m-%d").date()
        time = datetime.strptime(time_str, "%H:%M").time()
    except ValueError:
        raise ValueError("Invalid date or time format. Use YYYY-MM-DD and HH:MM.")

    scheduled_datetime = datetime.combine(date, time)

    # Prevent scheduling in the past
    if scheduled_datetime < datetime.now():
        raise ValueError("Cannot schedule a drive in the past.")

    # Prevent scheduling too far into the future
    max_days = datetime.now() + timedelta(days=60)
    if scheduled_datetime > max_days:
        raise ValueError("Cannot schedule a drive more than 60 days in advance.")

    # Prevent duplicate same-day drive on same area/street
    existing_drive = Drive.query.filter_by(
        areaId=area_id, streetId=street_id, date=date
    ).first()

    if existing_drive:
        raise ValueError("A drive is already scheduled for this area and street on this date.")

    # Process ETA if provided
    eta_time = None
    if eta_str:
        try:
            eta_time = datetime.strptime(eta_str, "%H:%M").time()
        except ValueError:
            raise ValueError("Invalid ETA format. Use HH:MM.")

    # Create drive
    new_drive = Drive(
        driverId=driver.id,
        areaId=area_id,
        streetId=street_id,
        date=date,
        time=time,
        status="Upcoming",
        menu=menu,
        eta=eta_time
    )

    db.session.add(new_drive)
    db.session.commit()

    # Notify subscribed residents
    new_drive.notify_new_drive()

    return new_drive


def driver_cancel_drive(driver, drive_id):
    drive = Drive.query.get(drive_id)

    if not drive or drive.driverId != driver.id:
        raise ValueError("Drive not found or you don't have permission.")

    return driver.cancel_drive(drive_id)


def driver_view_drives(driver):
    return [
        d for d in driver.view_drives()
        if d.status in ("Upcoming", "In Progress")
    ]


def driver_start_drive(driver, drive_id):
    # Check if driver already has an active drive
    active = Drive.query.filter_by(driverId=driver.id, status="In Progress").first()
    if active:
        raise ValueError(f"You are already on drive {active.id}.")

    drive = Drive.query.filter_by(
        driverId=driver.id,
        id=drive_id,
        status="Upcoming"
    ).first()

    if not drive:
        raise ValueError("Drive not found or cannot be started.")

    return driver.start_drive(drive_id)


def driver_end_drive(driver):
    active = Drive.query.filter_by(driverId=driver.id, status="In Progress").first()

    if not active:
        raise ValueError("No drive in progress.")

    return driver.end_drive(active.id)


def driver_view_requested_stops(driver, drive_id):
    stops = driver.view_requested_stops(drive_id)
    return stops or []



# EXTRA DRIVE UPDATES: MENU + ETA


def driver_update_drive_menu(driver, drive_id, menu):
    drive = Drive.query.get(drive_id)

    if not drive or drive.driverId != driver.id:
        raise ValueError("Drive not found or you don't have permission.")

    drive.set_menu_and_eta(menu, drive.eta)
    db.session.commit()

    return drive


def driver_update_drive_eta(driver, drive_id, eta_str):
    drive = Drive.query.get(drive_id)

    if not drive or drive.driverId != driver.id:
        raise ValueError("Drive not found or you don't have permission.")

    try:
        eta_time = datetime.strptime(eta_str, "%H:%M").time()
    except ValueError:
        raise ValueError("Invalid ETA format. Use HH:MM.")

    drive.set_menu_and_eta(drive.menu, eta_time)
    db.session.commit()

    return drive



# DRIVER STOCK MANAGEMENT

def driver_update_stock(driver, item_id, quantity):
    item = Item.query.get(item_id)
    if not item:
        raise ValueError("Invalid item ID.")

    stock = DriverStock.query.filter_by(
        driverId=driver.id,
        itemId=item_id
    ).first()

    if stock:
        stock.quantity = quantity
    else:
        stock = DriverStock(
            driverId=driver.id,
            itemId=item_id,
            quantity=quantity
        )
        db.session.add(stock)

    db.session.commit()
    return stock


def driver_view_stock(driver):
    return DriverStock.query.filter_by(driverId=driver.id).all()

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0  # Earth radius in km

    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

def notify_residents_of_arrival(driver):
    residents = Resident.query.filter_by(areaId=driver.areaId).all()

    for r in residents:
        # Skip if resident has no coordinates
        if not getattr(r, 'lat', None) or not getattr(r, 'lng', None):
            continue

        distance_km = haversine(driver.last_lat, driver.last_lng, r.lat, r.lng)

        if distance_km < 0.4:  # 400 meters
            r.receive_notif(
                "The Bread Van is near your area!",
                "arrival_alert",
                None
            )

    db.session.commit()

def update_driver_location(driver_id, lat, lng):

    driver = Driver.query.get(driver_id)
    if not driver:
        raise ValueError("Driver not found.")

    driver.last_lat = lat
    driver.last_lng = lng
    db.session.commit()

    # Notify residents nearby
    notify_residents_of_arrival(driver)

    return driver