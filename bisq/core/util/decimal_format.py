from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from decimal import Decimal

class DecimalFormat:
    def __init__(self, pattern="#.###", *, grouping_used = False, grouping_size = 3):
        """
        Initialize DecimalFormat with pattern similar to Java
        Args:
            pattern: Format pattern (default "#.###")
        """
        self.decimal_places = len(pattern.split('.')[1]) if '.' in pattern else 1
        self.min_fraction_digits = 0
        self.max_fraction_digits = self.decimal_places
        self.grouping_used = grouping_used
        self.grouping_size = grouping_size if grouping_size else 3

    def set_minimum_fraction_digits(self, digits):
        """Set the minimum number of digits allowed in the fraction portion"""
        self.min_fraction_digits = max(0, int(digits))
        if self.min_fraction_digits > self.max_fraction_digits:
            self.max_fraction_digits = self.min_fraction_digits

    def set_maximum_fraction_digits(self, digits):
        """Set the maximum number of digits allowed in the fraction portion"""
        self.max_fraction_digits = max(0, int(digits))
        if self.max_fraction_digits < self.min_fraction_digits:
            self.min_fraction_digits = self.max_fraction_digits

    def format(self, number: Union[int, float, Decimal]) -> str:
        """
        Format number according to the pattern
        Args:
            number: Number to format
        Returns:
            Formatted string
        """
        if number is None:
            return "0"
        
        # Round to maximum fraction digits
        rounded = round(float(number), self.max_fraction_digits)
        
        # Format with maximum digits
        formatted = f"{rounded:.{self.max_fraction_digits}f}"
        
        if self.min_fraction_digits == 0:
            # Remove trailing zeros and decimal point if allowed
            formatted = formatted.rstrip('0').rstrip('.')
        else:
            # Ensure minimum number of fraction digits
            parts = formatted.split('.')
            if len(parts) == 1:
                formatted += '.' + '0' * self.min_fraction_digits
            else:
                decimal_part = parts[1].ljust(self.min_fraction_digits, '0')
                formatted = f"{parts[0]}.{decimal_part}"
        
        # Apply grouping if enabled
        if self.grouping_used:
            parts = formatted.split('.')
            integer_part = parts[0]
            # Handle negative numbers
            sign = ''
            if integer_part.startswith('-'):
                sign = '-'
                integer_part = integer_part[1:]
            # Add group separators
            groups = []
            while integer_part:
                groups.insert(0, integer_part[-self.grouping_size:])
                integer_part = integer_part[:-self.grouping_size]
            integer_part = sign + ','.join(groups)
            formatted = integer_part + ('.' + parts[1] if len(parts) > 1 else '')
        
        return formatted