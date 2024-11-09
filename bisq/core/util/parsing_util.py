
def convert_chars_for_number(input_str: str) -> str:
    # Some languages like Finnish use the long dash for the minus
    input_str = input_str.replace('−', '-')
    # Remove all whitespace
    input_str = input_str.translate(str.maketrans('', '', ' \t\n\r'))
    # Replace comma with decimal point
    return input_str.replace(',', '.')
