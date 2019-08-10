import re
import datetime
from dateutil.relativedelta import relativedelta
from discord.ext import commands

"""
Note that converters are specific to discord py library
and will not work with regular python functions, only
discord py commands.

"""


def positive_integer(integer):
    """
    :param integer: type that can be casted to int
    :return: int(integer) if param integer is larger that 0
    :raise: commands.BadArgument if integer is < 1
    :raise: ValueError if param integer can't be converted to int

    """
    integer = int(integer)
    if integer < 1:
        raise commands.BadArgument("Passed argument has to be a integer larger than zero.")
    else:
        return integer


def time_string_to_hours(str_input: str) -> int:
    """
    :param str_input: string where each word is in one of supported formats (years, months, weeks, days, hours).
    Example inputs: 5y 3months 7h
                    3m 7weeks
                    5hours 3years
                    4w
    Each word has to contain integer + type format
    Formats are (separated by comma):years,y,months,m,weeks,w,days,d,hours,h

    :return: int representing hours that are converted from param str_input formats
    Example input/output:   5y 3months 7h   /   46063
                            3m 7weeks       /   3384
                            1w              /   168

    """
    compiled = re.compile("""(?:(?P<years>[0-9])(?:years?|y))?          # e.g. 2years or 2y
                             (?:(?P<months>[0-9]{1,2})(?:months?|m))?   # e.g. 2months or 2m
                             (?:(?P<weeks>[0-9]{1,4})(?:weeks?|w))?     # e.g. 10weeks or 10w
                             (?:(?P<days>[0-9]{1,5})(?:days?|d))?       # e.g. 14days or 10d
                             (?:(?P<hours>[0-9]{1,5})(?:hours?|h))?     # e.g. 12hours or 12h
                          """, re.VERBOSE)
    hours = 0
    for word in str_input.split():
        match = compiled.fullmatch(word)
        if match is None or not match.group(0):
            raise commands.BadArgument("Invalid time provided.")

        time_data = {k: int(v) for k, v in match.groupdict(default=0).items()}
        now = datetime.datetime.utcnow()
        td = (relativedelta(**time_data) + now) - now
        hours += td.days * 24 + td.seconds // 3600
    return hours


def license_duration(input_duration: str) -> int:
    """
    :param input_duration: str consisting of a positive integer or date duration format.
    :return: int representing license duration hours.
             Maximum allowed integer is 8784 representing 12 months.
    :raise: commands.BadArgument or discord.ext.commands.BadArgument (don't manually catch them, use error handler
            instead, since this is a converter)

    """
    max_hours = 8784
    try:
        duration = positive_integer(input_duration)
    except ValueError:
        duration = time_string_to_hours(input_duration)

    if duration > max_hours:
        raise commands.BadArgument(f"Duration can't be longer than {max_hours}h, currently it is {duration}h.")
    else:
        return duration
