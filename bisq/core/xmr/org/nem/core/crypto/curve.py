from abc import ABC, abstractmethod


class Curve(ABC):
    """Interface for getting information for a curve."""

    @abstractmethod
    def get_name(self):
        """
        Gets the name of the curve.

        :return: The name of the curve.
        """
        pass

    @abstractmethod
    def get_group_order(self):
        """
        Gets the group order.

        :return: The group order.
        """
        pass

    @abstractmethod
    def get_half_group_order(self):
        """
        Gets the group order / 2.

        :return: The group order / 2.
        """
        pass
