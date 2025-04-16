from math import sqrt
from bisq.core.exceptions.illegal_argument_exception import IllegalArgumentException


class InlierUtil:
    @staticmethod
    def find_inlier_range(
        y_values: list[float],
        percent_to_trim: float,
        how_many_std_devs_constitute_outlier: float,
    ):
        """
        Finds the minimum and maximum inlier values. The returned values may be NaN.
        See `compute_inlier_threshold` for the definition of inlier.
        """
        inlier_threshold = InlierUtil._compute_inlier_threshold(
            y_values, percent_to_trim, how_many_std_devs_constitute_outlier
        )

        inlier_values = [
            value
            for value in y_values
            if inlier_threshold[0] <= value <= inlier_threshold[1]
        ]

        if not inlier_values:
            return float("nan"), float("nan")

        inlier_min = min(inlier_values)
        inlier_max = max(inlier_values)

        return inlier_min, inlier_max

    @staticmethod
    def _compute_inlier_threshold(
        numbers: list[float],
        percent_to_trim: float,
        how_many_std_devs_constitute_outlier: float,
    ):
        """
        Computes the lower and upper inlier thresholds. A point lying outside
        these thresholds is considered an outlier, and a point lying within
        is considered an inlier.
        The thresholds are found by trimming the dataset (see method `trim`),
        then adding or subtracting a multiple of its (trimmed) standard
        deviation from its (trimmed) mean.
        """

        if how_many_std_devs_constitute_outlier <= 0:
            raise IllegalArgumentException(
                "how_many_std_devs_constitute_outlier should be a positive number"
            )

        trimmed = InlierUtil._trim(percent_to_trim, numbers)

        mean = sum(trimmed) / len(trimmed)
        variance = sum((x - mean) ** 2 for x in trimmed) / len(trimmed)
        std_dev = sqrt(variance)

        inlier_lower_threshold = mean - (std_dev * how_many_std_devs_constitute_outlier)
        inlier_upper_threshold = mean + (std_dev * how_many_std_devs_constitute_outlier)

        return inlier_lower_threshold, inlier_upper_threshold

    @staticmethod
    def _trim(percent_to_trim: float, numbers: list[float]):
        """
        Sorts the data and discards given percentage from the left and right sides each.
        E.g. 5% trim implies a total of 10% (2x 5%) of elements discarded.
        Used in calculating trimmed mean (and in turn trimmed standard deviation),
        which is more robust to outliers than a simple mean.
        """

        min_percent_to_trim = 0
        max_percent_to_trim = 50
        if not (min_percent_to_trim <= percent_to_trim <= max_percent_to_trim):
            raise IllegalArgumentException(
                f"The percentage of data points to trim must be in the range [{min_percent_to_trim},{max_percent_to_trim}]."
            )

        total_percent_trim = percent_to_trim * 2
        if total_percent_trim == 0:
            return numbers
        if total_percent_trim == 100:
            return []

        if not numbers:
            return numbers

        count = len(numbers)
        count_to_drop_from_each_side = round((count / 100) * percent_to_trim)
        if count_to_drop_from_each_side == 0:
            return numbers

        sorted_numbers = sorted(numbers)
        return sorted_numbers[
            count_to_drop_from_each_side : count - count_to_drop_from_each_side
        ]
