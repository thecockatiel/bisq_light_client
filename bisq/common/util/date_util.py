from datetime import datetime


class DateUtil:
    @staticmethod
    def get_start_of_month(date: datetime):
        """
        :param date: The date which should be reset to first day of month
        :return: First day in given date with time set to zero.
        """
        return datetime(date.year, date.month, 1)

    @staticmethod
    def get_start_of_year_month(year: int, month: int):
        """
        :param year: The year
        :param month: The month starts with 1 for January
        :return: First day in given month with time set to zero.
        """
        return datetime(year, month, 1)
