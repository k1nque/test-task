"""Script to populate database with test data."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from geoalchemy2.elements import WKTElement

from app.db.session import SessionLocal, engine
from app.models import Base, Building, Activity, Organization, OrganizationPhone


def create_test_data():
    """Create test data for the database."""
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    db: Session = SessionLocal()
    try:
        # Create buildings
        buildings_data = [
            {
                "address": "г. Москва, ул. Ленина 1, офис 3",
                "coordinates": WKTElement("POINT(37.6173 55.7558)", srid=4326),
            },
            {
                "address": "г. Москва, ул. Блюхера 32/1",
                "coordinates": WKTElement("POINT(37.5850 55.7344)", srid=4326),
            },
            {
                "address": "г. Новосибирск, пр. Красный 15",
                "coordinates": WKTElement("POINT(82.9346 55.0084)", srid=4326),
            },
            {
                "address": "г. Санкт-Петербург, Невский пр. 28",
                "coordinates": WKTElement("POINT(30.3609 59.9311)", srid=4326),
            },
            {
                "address": "г. Москва, ул. Арбат 10",
                "coordinates": WKTElement("POINT(37.5951 55.7520)", srid=4326),
            },
        ]
        
        buildings = []
        for building_data in buildings_data:
            building = Building(**building_data)
            db.add(building)
            buildings.append(building)
        
        db.flush()
        print(f"✓ Created {len(buildings)} buildings")
        
        # Create activities tree
        # Level 1
        food_activity = Activity(name="Еда", level=1)
        auto_activity = Activity(name="Автомобили", level=1)
        services_activity = Activity(name="Услуги", level=1)
        
        db.add_all([food_activity, auto_activity, services_activity])
        db.flush()
        
        # Level 2
        meat_activity = Activity(name="Мясная продукция", parent=food_activity, level=2)
        dairy_activity = Activity(name="Молочная продукция", parent=food_activity, level=2)
        truck_activity = Activity(name="Грузовые", parent=auto_activity, level=2)
        passenger_activity = Activity(name="Легковые", parent=auto_activity, level=2)
        cleaning_activity = Activity(name="Клининг", parent=services_activity, level=2)
        
        db.add_all([
            meat_activity, dairy_activity, truck_activity,
            passenger_activity, cleaning_activity
        ])
        db.flush()
        
        # Level 3
        parts_activity = Activity(name="Запчасти", parent=passenger_activity, level=3)
        accessories_activity = Activity(name="Аксессуары", parent=passenger_activity, level=3)
        
        db.add_all([parts_activity, accessories_activity])
        db.flush()
        
        print("✓ Created activity tree with 3 levels")
        
        # Create organizations
        orgs_data = [
            {
                "name": 'ООО "Рога и Копыта"',
                "building": buildings[0],
                "phones": ["2-222-222", "3-333-333", "8-923-666-13-13"],
                "activities": [meat_activity, dairy_activity],
            },
            {
                "name": 'АО "Молочные реки"',
                "building": buildings[1],
                "phones": ["8-800-555-35-35"],
                "activities": [dairy_activity, food_activity],
            },
            {
                "name": 'ИП Иванов "Мясная лавка"',
                "building": buildings[2],
                "phones": ["8-913-123-45-67", "8-913-765-43-21"],
                "activities": [meat_activity, food_activity],
            },
            {
                "name": 'ООО "АвтоМир"',
                "building": buildings[3],
                "phones": ["8-812-333-22-11"],
                "activities": [passenger_activity, parts_activity, accessories_activity],
            },
            {
                "name": 'ООО "ГрузАвто"',
                "building": buildings[1],
                "phones": ["8-495-111-22-33"],
                "activities": [truck_activity, auto_activity],
            },
            {
                "name": 'ИП Петрова "Чистый дом"',
                "building": buildings[4],
                "phones": ["8-926-777-88-99"],
                "activities": [cleaning_activity, services_activity],
            },
            {
                "name": 'ООО "Продукты Сибири"',
                "building": buildings[2],
                "phones": ["8-383-222-33-44", "8-383-555-66-77"],
                "activities": [food_activity, meat_activity, dairy_activity],
            },
            {
                "name": 'ООО "Автозапчасти Плюс"',
                "building": buildings[4],
                "phones": ["8-495-999-88-77"],
                "activities": [parts_activity],
            },
        ]
        
        for org_data in orgs_data:
            org = Organization(
                name=org_data["name"],
                building=org_data["building"],
            )
            
            # Add phone numbers
            for phone in org_data["phones"]:
                org_phone = OrganizationPhone(
                    organization_id=org.id,
                    phone_number=phone
                )
                org.phone_numbers.append(org_phone)
            
            # Add activities
            for activity in org_data["activities"]:
                org.activities.append(activity)
            
            db.add(org)
        
        db.commit()
        print(f"✓ Created {len(orgs_data)} organizations")
        print("\n✓ Test data created successfully!")
        
    except Exception as e:
        print(f"✗ Error creating test data: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("Creating test data...")
    create_test_data()
