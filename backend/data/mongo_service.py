from .mongo_repository import MongoRepository
from .dto import Weather, OSSD

class MongoService:
    """Database service layer with business logic"""
    
    def __init__(self):
        """Initialize all MongoDB repositories"""
        self.weather = MongoRepository("weather", Weather)
        self.ossd = MongoRepository("ossd", OSSD)