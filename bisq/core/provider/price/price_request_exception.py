class PriceRequestException(Exception):
    def __init__(self, exception_or_msg=None, price_provider_base_url=None):
        super().__init__(str(exception_or_msg))
        self.price_provider_base_url = price_provider_base_url
