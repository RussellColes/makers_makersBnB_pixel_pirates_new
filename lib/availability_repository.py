from lib.availability import Availability
import datetime


class AvailabilityRepository:
    # We initialise with a database connection
    def __init__(self, connection):
        self._connection = connection

    # Retrieve all availabilities
    def all(self):
        rows = self._connection.execute('SELECT * FROM availabilities')
        availabilities = []
        for row in rows:
            date_str = row["date"].strftime('%Y-%m-%d') if isinstance(row["date"], datetime.date) else row["date"]
            item = Availability(row["id"], row["space_id"], date_str, row["is_available"])
            availabilities.append(item)
        return availabilities
    
    
    def find(self, id):
        rows = self._connection.execute(
            'SELECT * from availabilities WHERE id = %s', [id])
        row = rows[0]
        date_str = row["date"].strftime('%Y-%m-%d') if isinstance(row["date"], datetime.date) else row["date"]
        return Availability(row["id"], row["space_id"], date_str, row["is_available"])
    
    def create(self, availability):
        rows = self._connection.execute(
            'INSERT INTO availabilities (space_id, date, is_available) VALUES (%s, %s, %s) RETURNING id', 
            [availability.space_id, availability.date, availability.is_available])
        row = rows[0]
        availability.id = row["id"]
        return availability

    
    def delete(self, id):
        self._connection.execute('DELETE FROM availabilities WHERE id = %s', [id])
        return None
    
    def find_only_if_available(self, space_id):
        rows = self._connection.execute('SELECT * from availabilities WHERE is_available = True and space_id = %s', [space_id])
        availabilities = []
        for row in rows:
            date_str = row["date"].strftime('%Y-%m-%d') if isinstance(row["date"], datetime.date) else row["date"]
            item = Availability(row["id"], row["space_id"], date_str, row["is_available"])
            availabilities.append(item)
        return availabilities
    
    def update_by_date_range(self, space_id, start_date, end_date):
        self._connection.execute('UPDATE availabilities SET is_available = False WHERE space_id = %s AND date BETWEEN %s and %s', [space_id, start_date, end_date])
        return None
    
    
    