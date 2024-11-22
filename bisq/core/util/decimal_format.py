class DecimalFormat:
    def __init__(self, pattern="#.###"):
        """
        Initialize DecimalFormat with pattern similar to Java
        Args:
            pattern: Format pattern (default "#.###")
        """
        self.decimal_places = len(pattern.split('.')[1]) if '.' in pattern else 1
        self.min_fraction_digits = 0
        self.max_fraction_digits = self.decimal_places

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

    def format(self, number):
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
        
        return formatted