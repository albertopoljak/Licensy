"""
Note that converters are specific to discord py library
and will not work with regular python functions, only
discord py commands.

"""


def positive_integer(integer):
    """
    Used as argument converter, example:
        @commands.command()
        async def divide(a: int, b: positive_integer):
    :param integer: type that can be casted to int
    :return: int(integer) if param integer is larger that 0
    :raise: AttributeError if integer is < 1

    """
    integer = int(integer)
    if integer < 1:
        raise AttributeError("Passed argument has to be a integer larger than zero.")
    else:
        return integer


def license_duration(input_duration: str) -> int:
    """
    Currently just checks if passed string is a positive integer
    and returns it if it is.

    :return: int representing hours

    TODO: Input in various formats aka 1w2d or 59h23m or 120m or 1week2days
    """

    input_duration = positive_integer(input_duration)
    return input_duration
