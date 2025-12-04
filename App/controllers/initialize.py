from App.database import db
from App.models import Driver, Resident, Area, Street
from App.database import db
from App.models import Driver, Resident, Area, Street
from App.controllers.area import create_area
from App.controllers.street import create_street
from App.controllers.driver import create_driver, delete_driver
from App.controllers.resident import resident_create



def initialize():
    db.drop_all()
    db.create_all()



    #Creating Areas and Streets

    area1 = create_area('St. Augustine')
    db.session.add(area1)
    db.session.commit()

    
    street11 = create_street(name="Gordon Street", areaId=area1.id)
    street12 = create_street(name="Warner Street", areaId=area1.id)
    street13 = create_street(name="College Road", areaId=area1.id)
    db.session.add_all([street11, street12, street13])
    db.session.commit()

    area2 = create_area(name='Tunapuna')
    db.session.add(area2)
    db.session.commit()
     
    street21 = create_street(name="Fairly Street", areaId=area2.id)
    street22 = create_street(name="Saint John Road", areaId=area2.id)
    db.session.add_all([street21, street22])
    db.session.commit()

    area3 = create_area(name='San Juan')
    db.session.add(area3)
    db.session.commit()

    #Creating Drivers
    driver1 = create_driver(username="bob",
                     password="bobpass",
                     status="Offline",
                     areaId=area1.id,
                     streetId=street11.id)
    driver2 = create_driver(username="mary",
                     password="marypass",
                     status="Available",
                     areaId=area2.id,
                     streetId=None)
    db.session.add_all([driver1, driver2])
    db.session.commit()

    #Creating Residents and Stops
    resident1 = resident_create(username="alice",
                         password="alicepass",
                         areaId=area1.id,
                         streetId=street12.id,
                         houseNumber=48)
    resident2 = resident_create(username="jane",
                         password="janepass",
                         areaId=area1.id,
                         streetId=street12.id,
                         houseNumber=50)
    resident3 = resident_create(username="john",
                         password="johnpass",
                         areaId=area2.id,
                         streetId=street22.id,
                         houseNumber=13)
    
    # Added new resident with house number 6
    resident4 = resident_create(username="sam",
                         password="sampass",
                         areaId=area1.id,
                         streetId=street13.id,
                         houseNumber=6)  # Adding number 6 here
    
    db.session.add_all([resident1, resident2, resident3, resident4])  # Updated to include resident4
    db.session.commit()

    #Creating Drives and Stops
    driver2.schedule_drive(area1.id, street12.id, "2025-10-26", "10:00")
    db.session.commit()
                     
    resident2.request_stop(0)
    db.session.commit()