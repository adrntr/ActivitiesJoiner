from models import Location


def get_location(session, latitude, longitude):
    return session.query(Location).filter(Location.latitude == latitude, Location.longitude == longitude).first()

def create_location(session, name, latitude, longitude):
    location = Location(name=name, latitude=latitude, longitude=longitude)
    session.add(location)
    session.commit()
    session.refresh(location)
    return location

