import os, tempfile, pytest, logging, unittest
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import date, time, datetime, timedelta
from unittest.mock import MagicMock, patch

from App.main import create_app
from App.database import db, create_db
from App.models import User, Resident, Driver, Area, Street, Drive, Stop, Item, DriverStock

from App.controllers.area import create_area, get_all_areas, get_area_by_id, get_streets_in_area, delete_area
from App.controllers.street import create_street, get_street_by_id, get_all_streets, delete_street, get_streets_by_name
from App.controllers.item import add_item, get_item_by_id, get_all_items, delete_item, get_items_by_name, get_items_by_tag, update_item
from App.controllers.driver import create_driver, delete_driver
from App.controllers.resident import resident_create
from App.controllers.user import create_user, get_user_by_username, get_user, get_all_users, get_all_users_json, update_user, user_login, user_logout, user_view_street_drives
from App.controllers.stop import create_stop, get_stops_by_drive, get_stops_by_resident, delete_stop, get_all_stops, get_stops_by_drive_and_resident
from App.controllers.drive import add_drive, get_drives_by_area_and_street, get_upcoming_drives, delete_drive, get_drives_by_driver, get_drives_by_status, get_drives_scheduled_between, get_all_drives, get_drives_by_area, get_drives_by_street, get_drives_by_date

from App.controllers.driver import (
    driver_schedule_drive, driver_cancel_drive, driver_update_drive_eta,
    driver_view_drives, driver_start_drive, driver_end_drive,
    driver_view_requested_stops, driver_update_stock, driver_view_stock,
    driver_update_drive_menu
)

from App.controllers.resident import (
    resident_request_stop, resident_cancel_stop, resident_view_inbox,
    resident_view_driver_stats, resident_subscribe_to_drive,
    resident_unsubscribe_from_drive, resident_get_subscribed_drives,
    resident_get_notifications, resident_get_notification_stats,
    resident_mark_notification_read, resident_mark_all_notifications_read,
    resident_clear_notifications, resident_update_notification_preferences,
    resident_request_stop_from_notification, resident_view_stock
)


LOGGER = logging.getLogger(__name__)

'''
   Unit Tests
'''
class UserUnitTests(unittest.TestCase):

    def test_new_user(self):
        user = User("bob", "bobpass")
        assert user.username == "bob"

    # pure function no side effects or integrations called
    def test_user_getJSON(self):
        user = User("bob", "bobpass")
        user_json = user.get_json()
        self.assertDictEqual(user_json, {"id":None, "username":"bob"})
    
    def test_hashed_password(self):
        password = "mypass"
        hashed = generate_password_hash(password, method='pbkdf2:sha256')
        newuser = User("bob", password)
        assert newuser.password != password

    def test_check_password(self):
        password = "mypass"
        user = User("bob", password)
        assert user.check_password(password)

class ResidentUnitTests(unittest.TestCase):

    def test_new_resident(self):
        resident = Resident("john", "johnpass", 1, 2, 123)
        assert resident.username == "john"
        assert resident.password != "johnpass"
        assert resident.areaId == 1
        assert resident.streetId == 2
        assert resident.houseNumber == 123
        assert resident.inbox == []

    def test_resident_type(self):
        resident = Resident("john", "johnpass", 1, 2, 123)
        assert resident.type == "Resident"

    def test_resident_getJSON(self):
        resident = Resident("john", "johnpass", 1, 2, 123)
        resident_json = resident.get_json()
        expected = {
            'id': None,
            'username': 'john',
            'areaId': 1,
            'streetId': 2,
            'houseNumber': 123,
            'inbox': [],
            'notification_preferences': ['drive_scheduled', 'menu_updated', 'eta_updated'],
            'subscribed_drives': []
        }
        self.assertDictEqual(resident_json, expected)

    def test_receive_notif(self):
        resident = Resident("john", "johnpass", 1, 2, 123)
        resident.receive_notif("New msg")
        assert len(resident.inbox) == 1
        notification = resident.inbox[0]
        self.assertIn("New msg", notification["message"])

    def test_view_inbox(self):
        resident = Resident("john", "johnpass", 1, 2, 123)
        resident.receive_notif("msg1")
        resident.receive_notif("msg2")
        assert len(resident.inbox) == 2
        self.assertIn("msg1", resident.inbox[0]["message"])
        self.assertIn("msg2", resident.inbox[1]["message"])
        
class DriverUnitTests(unittest.TestCase):

    def test_new_driver(self):
        driver = Driver("steve", "stevepass", "Busy", 2, 12)
        assert driver.username == "steve"
        assert driver.password != "stevepass"
        assert driver.status == "Busy"
        assert driver.areaId == 2
        assert driver.streetId == 12
        
    def test_driver_type(self):
        driver = Driver("steve", "stevepass", "Busy", 2, 12)
        assert driver.type == "Driver"

    def test_driver_getJSON(self):
        driver = Driver("steve", "stevepass", "Busy", 2, 12)
        
        # Test get_json with mocked relationships using patch
        with patch.object(driver, 'area', None), patch.object(driver, 'street', None):
            driver_json = driver.get_json()
            
            # Check the required fields are present
            self.assertEqual(driver_json['username'], 'steve')
            self.assertEqual(driver_json['status'], 'Busy')
            # area and street will be None since relationships aren't loaded
            self.assertIsNone(driver_json.get('area'))
            self.assertIsNone(driver_json.get('street'))

class AreaUnitTests(unittest.TestCase):

    def test_new_area(self):
        area = Area("Sangre Grande")
        assert area.name == "Sangre Grande"

    def test_area_getJSON(self):
        area = Area("Sangre Grande")
        area_json = area.get_json()
        self.assertDictEqual(area_json, {"id":None, "name":"Sangre Grande"})

class StreetUnitTests(unittest.TestCase):

    def test_new_street(self):
        street = Street("Picton Road", 8)
        assert street.name == "Picton Road"
        assert street.areaId == 8

    def test_street_getJSON(self):
        street = Street("Picton Road", 8)
        street_json = street.get_json()
        self.assertDictEqual(street_json, {"id":None, "name":"Picton Road", "areaId":8})

class DriveUnitTests(unittest.TestCase):

    def test_new_drive(self):
        drive = Drive(78, 2, 12, date(2025, 11, 8), time(11, 30), "Upcoming")
        assert drive.driverId == 78
        assert drive.areaId == 2
        assert drive.streetId == 12
        assert drive.date == date(2025, 11, 8)
        assert drive.time == time(11, 30)
        assert drive.status == "Upcoming"

    def test_drive_getJSON(self):
        drive = Drive(78, 2, 12, date(2025, 11, 8), time(11, 30), "Upcoming")
        drive_json = drive.get_json()
        
        self.assertEqual(drive_json['driverId'], 78)
        self.assertEqual(drive_json['areaId'], 2)
        self.assertEqual(drive_json['streetId'], 12)
        self.assertEqual(drive_json['status'], 'Upcoming')
        self.assertEqual(drive_json['menu'], None)
        self.assertEqual(drive_json['eta'], None)
        self.assertIsInstance(drive_json['date'], (date, str))
        self.assertIsInstance(drive_json['time'], (time, str))

class StopUnitTests(unittest.TestCase):

    def test_new_stop(self):
        stop = Stop(1, 2)
        assert stop.driveId == 1
        assert stop.residentId == 2

    def test_stop_getJSON(self):
        stop = Stop(1, 2)
        stop_json = stop.get_json()
        self.assertDictEqual(stop_json, {"id":None, "driveId":1, "residentId":2})

class ItemUnitTests(unittest.TestCase):

    def test_new_item(self):
        item = Item("Whole-Grain Bread", 19.50, "Healthy whole-grain loaf", ["whole-grain", "healthy"])
        assert item.name == "Whole-Grain Bread"
        assert item.price == 19.50
        assert item.description == "Healthy whole-grain loaf"
        assert item.tags == ["whole-grain", "healthy"]

    def test_item_getJSON(self):
        item = Item("Whole-Grain Bread", 19.50, "Healthy whole-grain loaf", ["whole-grain", "healthy"])
        item_json = item.get_json()
        self.assertDictEqual(item_json, {"id":None, "name":"Whole-Grain Bread", "price":19.50, "description":"Healthy whole-grain loaf", "tags":["whole-grain", "healthy"]})

class DriverStockUnitTests(unittest.TestCase):

    def test_new_driverStock(self):
        driverStock = DriverStock(1, 2, 30)
        assert driverStock.driverId == 1
        assert driverStock.itemId == 2
        assert driverStock.quantity == 30

    def test_driverStock_getJSON(self):
        driverStock = DriverStock(1, 2, 30)
        driverStock_json = driverStock.get_json()
        self.assertDictEqual(driverStock_json, {"id":None, "driverId":1, "itemId":2, "quantity":30})
        

'''
    Integration Tests
'''

# This fixture creates an empty database for the test and deletes it after the test
# scope="class" would execute the fixture once and resued for all methods in the class
@pytest.fixture(autouse=True, scope="function")
def empty_db():
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
    db.create_all()    
    yield app.test_client()
    db.drop_all()


class UsersIntegrationTests(unittest.TestCase):

    def test_create_user(self):
        user = create_user("rick", "ronniepass")
        assert user.username == "rick"

    def test_get_all_users_json(self):
        create_user("bob", "bobpass")
        create_user("rick", "ronniepass")
        users_json = get_all_users_json()

        user_dict = {user['username']: user for user in users_json}
        self.assertIn("bob", user_dict)
        self.assertIn("rick", user_dict)

    # Tests data changes in the database
    def test_update_user(self):
        create_user("rick", "ronniepass")
        update_user(1, "ronnie")
        user = get_user(1)
        assert user.username == "ronnie"

    def test_login(self):
        create_user("ronnie", "ronniepass")
        user = user_login("ronnie", "ronniepass")
        assert user.username == "ronnie"

    def test_logout(self):
        create_user("ronnie", "ronniepass")
        user = user_login("ronnie", "ronniepass")
        user_logout(user)
        assert user.logged_in == False


class ResidentsIntegrationTests(unittest.TestCase):
    
    def setUp(self):
        self.area = create_area("St. Augustine")
        self.street = create_street(self.area.id, "Warner Street")
        
        self.driver = create_driver("driver1", "pass", "Available", self.area.id, self.street.id)
        
        self.resident = resident_create("john", "johnpass", self.area.id, self.street.id, 123)
        
        # Schedule a drive with FUTURE date
        future_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        self.drive = driver_schedule_drive(self.driver, self.area.id, self.street.id, future_date, "11:30")
        
        self.item = add_item("Whole-Grain Bread", 19.50, "Healthy whole-grain loaf", ["whole-grain", "healthy"])


    def test_request_stop(self):
        stop = resident_request_stop(self.resident, self.drive.id)
        self.assertIsNotNone(stop)

    def test_cancel_stop(self):
        stop = resident_request_stop(self.resident, self.drive.id)
        resident_cancel_stop(self.resident, self.drive.id)
        existing_stop = Stop.query.filter_by(driveId=self.drive.id, residentId=self.resident.id).first()
        self.assertIsNone(existing_stop)

    def test_view_driver_stats(self):
        driver = resident_view_driver_stats(self.resident, self.driver.id)
        self.assertIsNotNone(driver)

    def test_view_stock(self):
        driver_update_stock(self.driver, self.item.id, 30)
        stocks = resident_view_stock(self.resident, self.driver.id)
        self.assertIsNotNone(stocks)


class DriversIntegrationTests(unittest.TestCase):
                
    def setUp(self):
        self.area = create_area("St. Augustine")
        self.street = create_street(self.area.id, "Warner Street")
        
        self.driver = create_driver("driver1", "pass", "Available", self.area.id, self.street.id)
        
        self.resident = resident_create("john", "johnpass", self.area.id, self.street.id, 123)
        
        future_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        self.drive = driver_schedule_drive(self.driver, self.area.id, self.street.id, future_date, "11:30")
        
        self.stop = resident_request_stop(self.resident, self.drive.id)
        
        self.item = add_item("Whole-Grain Bread", 19.50, "Healthy whole-grain loaf", ["whole-grain", "healthy"])

    def test_schedule_drive(self):
        future_date = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
        drive = driver_schedule_drive(self.driver, self.area.id, self.street.id, future_date, "09:00")
        self.assertIsNotNone(drive)

    def test_cancel_drive(self):
        driver_cancel_drive(self.driver, self.drive.id)
        cancelled_drive = Drive.query.get(self.drive.id)
        self.assertEqual(cancelled_drive.status, "Cancelled")

    def test_view_drives(self):
        drives = driver_view_drives(self.driver)
        self.assertIsNotNone(drives)

    def test_start_drive(self):
        driver_start_drive(self.driver, self.drive.id)
        db.session.refresh(self.drive)
        db.session.refresh(self.driver)
        self.assertEqual(self.drive.status, "In Progress")
        self.assertEqual(self.driver.status, "Busy")

    def test_end_drive(self):
        driver_start_drive(self.driver, self.drive.id)
        driver_end_drive(self.driver)
        db.session.refresh(self.drive)
        db.session.refresh(self.driver)
        self.assertEqual(self.drive.status, "Completed")
        self.assertEqual(self.driver.status, "Available")

    def test_view_requested_stops(self):
        stops = driver_view_requested_stops(self.driver, self.drive.id)
        self.assertIsNotNone(stops)
    
    def test_update_stock(self):
        newquantity = 30
        driver_update_stock(self.driver, self.item.id, newquantity)
        stock = DriverStock.query.filter_by(driverId=self.driver.id, itemId=self.item.id).first()
        self.assertEqual(stock.quantity, newquantity)

    def test_view_stock(self):
        driver_update_stock(self.driver, self.item.id, 30)
        stock = driver_view_stock(self.driver)
        self.assertIsNotNone(stock)


class AreaIntegrationTests(unittest.TestCase):
    
    def test_create_area(self):
        area = create_area("Port-of-Spain")
        self.assertIsNotNone(area)
        self.assertEqual(area.name, "Port-of-Spain")

    def test_delete_area(self):
        area = create_area("Port-of-Spain")
        area_id = area.id
        delete_area(area_id)
        deleted_area = Area.query.get(area_id)
        self.assertIsNone(deleted_area)

    def test_view_all_areas(self):
        create_area("Port-of-Spain")
        create_area("Arima")
        create_area("San Fernando")
        areas = get_all_areas()
        self.assertIsNotNone(areas)
        self.assertGreaterEqual(len(areas), 3)

    def test_add_street(self):
        area = create_area("Port-of-Spain")
        street = create_street(area.id, "Fredrick Street")
        self.assertIsNotNone(street)
        self.assertEqual(street.name, "Fredrick Street")

    def test_delete_street(self):
        area = create_area("Port-of-Spain")
        street = create_street(area.id, "Fredrick Street")
        street_id = street.id
        delete_street(area.id, street_id)
        deleted_street = Street.query.get(street_id)
        self.assertIsNone(deleted_street)

    def test_view_all_streets(self):
        area = create_area("Port-of-Spain")
        create_street(area.id, "Fredrick Street")
        create_street(area.id, "Warner Street")
        create_street(area.id, "St. Vincent Street")
        streets = get_all_streets()
        self.assertIsNotNone(streets)
        self.assertGreaterEqual(len(streets), 3)


class ItemIntegrationTests(unittest.TestCase):
    
    def test_add_item(self):
        item = add_item("Whole-Grain Bread", 19.50, "Healthy whole-grain loaf", ["whole-grain", "healthy"])
        self.assertIsNotNone(item)
        self.assertEqual(item.name, "Whole-Grain Bread")

    def test_delete_item(self):
        item = add_item("Whole-Grain Bread", 19.50, "Healthy whole-grain loaf", ["whole-grain", "healthy"])
        item_id = item.id
        delete_item(item_id)
        deleted_item = Item.query.get(item_id)
        self.assertIsNone(deleted_item)

    def test_view_all_items(self):
        add_item("Whole-Grain Bread", 19.50, "Healthy whole-grain loaf", ["whole-grain", "healthy"])
        add_item("White Milk Bread", 12.00, "Soft and fluffy white milk bread", ["white", "soft"])
        add_item("Whole-Wheat Bread", 15.00, "Nutritious whole-wheat bread", ["whole-wheat", "nutritious"])
        items = get_all_items()
        self.assertIsNotNone(items)
        self.assertGreaterEqual(len(items), 3)


class StreetIntegrationTests(unittest.TestCase):
    
    def test_get_streets_by_name(self):
        area = create_area("Test Area")
        create_street(area.id, "Main Street")
        create_street(area.id, "Main Street East")
        create_street(area.id, "Broad Street")
        
        streets = get_streets_by_name("Main")
        self.assertEqual(len(streets), 2)
        street_names = [street.name for street in streets]
        self.assertIn("Main Street", street_names)
        self.assertIn("Main Street East", street_names)


class ResidentNotificationTests(unittest.TestCase):
    
    def setUp(self):
        self.area = create_area("Test Area")
        self.street = create_street(self.area.id, "Test Street")
        self.resident = resident_create("testuser", "testpass", self.area.id, self.street.id, 123)
        self.driver = create_driver("testdriver", "driverpass", "Available", self.area.id, self.street.id)
    
    def test_resident_subscribe_to_drive(self):
        future_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        drive = driver_schedule_drive(self.driver, self.area.id, self.street.id, future_date, "10:00")
        result = resident_subscribe_to_drive(self.resident, drive.id)
        self.assertTrue(result)
    
    def test_resident_unsubscribe_from_drive(self):
        future_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        drive = driver_schedule_drive(self.driver, self.area.id, self.street.id, future_date, "10:00")
        resident_subscribe_to_drive(self.resident, drive.id)
        result = resident_unsubscribe_from_drive(self.resident, drive.id)
        self.assertTrue(result)
    
    def test_resident_notification_preferences(self):
        new_preferences = ["drive_scheduled", "eta_updated"]
        resident_update_notification_preferences(self.resident, new_preferences)
        self.assertEqual(self.resident.notification_preferences, new_preferences)
    
    def test_resident_get_notification_stats(self):
        self.resident.receive_notif("Test message 1", "test_type")
        self.resident.receive_notif("Test message 2", "test_type")
        
        self.resident.mark_notification_read(0)
        
        db.session.commit()
        
        # Refresh resident from database
        db.session.refresh(self.resident)
        
        stats = resident_get_notification_stats(self.resident)
        self.assertEqual(stats["total_notifications"], 2)
        self.assertEqual(stats["unread_notifications"], 1)

