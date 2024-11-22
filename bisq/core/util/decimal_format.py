class DecimalFormat:
    def __init__(self, pattern="#.#"):
        """
        Initialize DecimalFormat with pattern similar to Java
        Args:
            pattern: Format pattern (default "#.#")
        """
        self.decimal_places = len(pattern.split('.')[1]) if '.' in pattern else 1

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
        
        # Round to specified decimal places
        rounded = round(float(number), self.decimal_places)
        
        # Convert to string with fixed decimal places
        formatted = f"{rounded:.{self.decimal_places}f}"
        
        # Remove trailing zeros and decimal point if no decimals
        formatted = formatted.rstrip('0').rstrip('.')
        
        return formatted