def positive_integer(integer):
    """
    Used as argument converter, example:
        def divide(a: int, b: positive_integer)

    :param integer: type that can be casted to int
    :return: int(integer) if param integer is larger that 0
    :raise: AttributeError if integer is < 1

    """
    integer = int(integer)
    if integer < 1:
        raise AttributeError("Passed argument has to be a integer larger than zero.")
    else:
        return integer
