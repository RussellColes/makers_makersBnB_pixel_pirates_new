class Space:
    def __init__(self, id, title, location, headline_description, description, price_per_night, user_id):
        self.id = id
        self.title = title
        self.location = location
        self.headline_description = headline_description
        self.description = description
        self.price_per_night = price_per_night
        self.user_id = user_id
    
    def __eq__(self, other):
        return self.__dict__ == other.__dict__

   
    def __repr__(self):
        return f"Space({self.id}, {self.title}, {self.location}, {self.headline_description}, {self.description}, {self.price_per_night}, {self.user_id})"