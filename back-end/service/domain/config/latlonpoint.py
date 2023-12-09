class LatLonPoint:
    """
    Latitude and longitude point object
    """
    def __init__(self, data: dict = None):
        """
        Initialize the lat/lon point
        """
        # initialize the properties
        self.latitude: float = 0
        self.longitude: float = 0

        # initialize from data if provided
        if data is not None:
            self.data = data

    @property
    def data(self) -> dict:
        """
        Get the data dictionary
        :return: A dictionary with all attributes
        """
        return {
            'latitude': self.latitude,
            'longitude': self.longitude
        }

    @data.setter
    def data(self, data: dict):
        """
        Set the full or partial set of attributes
        :param data: Values to set
        """
        self.latitude = self.latitude if 'latitude' not in data else data['latitude']
        self.longitude = self.longitude if 'longitude' not in data else data['longitude']
