from models import Location


def get(session, latitude, longitude):
    return session.query(Location).filter(Location.latitude == latitude, Location.longitude == longitude).first()

def create(session, location):
    #TODO: is is the same that activity...
    session.add(location)
    session.commit()
    session.refresh(location)
    return location

