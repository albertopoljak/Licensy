def positive_integer(integer):
    """
    Used as argument converter, example:
        @commands.command()
        async def divide(a: int, b: positive_integer):
    Note that converters are specific to discord py library
    and will not work with regular python functions, only
    discord py commands.

    :param integer: type that can be casted to int
    :return: int(integer) if param integer is larger that 0
    :raise: AttributeError if integer is < 1

    """
    integer = int(integer)
    if integer < 1:
        raise AttributeError("Passed argument has to be a integer larger than zero.")
    else:
        return integer
