from abc import ABC, abstractmethod

class Monetary(ABC):
    """
    Abstract base class representing a monetary value, such as a Bitcoin or fiat amount.
    """
    
    @abstractmethod
    def smallest_unit_exponent(self) -> int:
        """
        Returns the absolute value of exponent of the value of a "smallest unit" in scientific notation.
        For Bitcoin, a satoshi is worth 1E-8 so this would be 8.
        """
        pass

    @abstractmethod
    def get_value(self) -> int:
        """
        Returns the number of "smallest units" of this monetary value.
        For Bitcoin, this would be the number of satoshis.
        """
        pass

    @abstractmethod
    def signum(self) -> int:
        pass