from asyncio import TimeoutError

_MAX_MSG_SIZE = 2000
_ARROW_TO_BEGINNING = "\u23ee"
_ARROW_BACKWARD = "\u25c0"
_ARROW_FORWARD = "\u25b6"
_ARROW_TO_END = "\u23ed"
_PAGINATION_EMOJIS = (_ARROW_TO_BEGINNING, _ARROW_BACKWARD, _ARROW_FORWARD, _ARROW_TO_END)
_TIMEOUT = 120


class Paginator:
    """
    Made my own paginator because all others use embeds for output.
    Embeds are hell and I mostly need monospaced codeblocks.
    (and codeblock in embed for some darn reason limits it's line length making my output broken).
    It would be prettier to use embeds but as they really don't like codeblocks I was forced to make this.

    """

    @classmethod
    async def paginate(cls, bot, user, output, string, title="", separator="\n", prefix="```", suffix="```"):
        """"
        Can't use await in __init__ so we create a factory pattern.
        To correctly create this object you need to call :
            await Paginator.paginate()

        :param bot: our discord bot object. Used for wait_for
        :param user: discord member/user object who invoked the command which output is going to be paginated.
                     Used for checking if the reaction added to navbar is from this member (only he can
                     navigate trough paginator)
        :param output: discord channel/user to where the paginator is going to be sent
        :param string: string to paginate
        :param title: Shows at the top of every page of paginator
        :param separator: string which we will use to break apart param string.
        :param prefix: string prefix of every page of paginator, example "```"
        :param suffix: string suffix of every page of paginator, example "```"

        """
        self = Paginator(user, output, string, title, separator, prefix, suffix)
        await self.make_message()
        await self.start_listener(bot, user, self.message)

    def __init__(self, user, output, string, title, separator, prefix, suffix):
        self.user = user
        self.output = output
        self.prefix = prefix
        self.suffix = suffix
        self._max_msg_size = _MAX_MSG_SIZE - len(prefix) - len(suffix) - len(title) - Paginator.page_counter_suffix_string_length()
        self.chunk_index = 0
        self.chunks = Paginator.make_chunks(title, string, separator, self._max_msg_size)
        self.paginating = sum(map(len, self.chunks)) > self._max_msg_size
        self.message = None

    @staticmethod
    def make_chunks(title, string, separator, max_msg_size):
        """
        Basically splits param string based on param separator and adds each entry from that list
        to a temp list. Once the length of that temp list is going to exceed the param max_msg_size
        (not the length of list but the combined length of string elements in that temp list)
        add it to constructed_chunks and reset temp list.
        Repeat until done.

        Also deals with elements which are too long even after split by calling function break_long_entries.

        Returns constructed_chunks
        """
        constructed_chunks = []
        chunk_list = string.split(separator)
        Paginator.break_long_entries(chunk_list, max_msg_size)
        temp_chunk = []
        for entry in chunk_list:
            # len(temp_chunk) is because we'll add separators in join
            if sum(map(len, temp_chunk)) + len(entry) + len(temp_chunk) >= max_msg_size:
                constructed_chunks.append(title + separator.join(temp_chunk))
                temp_chunk = [entry]
            else:
                temp_chunk.append(entry)

        # For leftovers
        constructed_chunks.append(title + separator.join(temp_chunk))
        return constructed_chunks

    @staticmethod
    def break_long_entries(chunk_list, max_msg_size):
        """
        We further break down chunk_list in case any of the entries are larger than max_msg_size
        Modifies passed list in place!
        Will throw RecursionError if the string length in list is mega-huge.
        Basically when the entry is found just split it in half and re-add it in list without breaking order.
        Split in half will be done as many times as needed as long as resulting entry is larger than max_msg_size
        :param chunk_list: list of strings
        :param max_msg_size: integer, if entry is larger that this we break it down

        """
        for i, entry in enumerate(chunk_list):
            if len(entry) >= max_msg_size:
                # Split string in 2 parts by the middle
                f, s = entry[:len(entry)//2], entry[len(entry)//2:]
                # Append them back to our list, not breaking order
                chunk_list[i] = s
                chunk_list.insert(i, f)
                # Keep doing that until there is no entries that are larger in length than max_msg_size
                Paginator.break_long_entries(chunk_list, max_msg_size)

    def page_counter_suffix(self):
        page_count = f"Page[{self.chunk_index + 1}/{len(self.chunks)}]"
        return f"\n\n{page_count}{self.suffix}"

    @staticmethod
    def page_counter_suffix_string_length():
        """Format 'Page[000/999]"""
        return 13

    async def make_message(self):
        if self.paginating:
            self.message = await self.output.send(f"{self.prefix}{self.chunks[0]}{self.page_counter_suffix()}")
            await self._add_reactions()
        else:
            # Don't add counter if there is only 1 page
            self.message = await self.output.send(f"{self.prefix}{self.chunks[0]}{self.suffix}")

    async def _add_reactions(self):
        for emoji in _PAGINATION_EMOJIS:
            await self.message.add_reaction(emoji)

    async def clear_reactions(self):
        try:
            await self.message.clear_reactions()
        except Exception:
            # Silently ignore if no permission to remove reaction.
            pass

    async def update_message(self):
        await self.message.edit(content=f"{self.prefix}{self.chunks[self.chunk_index]}{self.page_counter_suffix()}")

    async def _remove_reaction(self, reaction):
        try:
            await self.message.remove_reaction(reaction, self.user)
        except Exception:
            # Silently ignore if no permission to remove reaction. (example DM)
            pass

    async def start_listener(self, bot, user, message):
        def react_check(reaction_, user_):
            return str(reaction_) in _PAGINATION_EMOJIS and user_.id == user.id and reaction_.message.id == message.id

        while self.paginating:
            try:
                reaction, user = await bot.wait_for("reaction_add", check=react_check, timeout=_TIMEOUT)
            except TimeoutError:
                self.paginating = False
                await self.clear_reactions()
                break

            if str(reaction) == _ARROW_TO_BEGINNING:
                if self.chunk_index == 0:
                    await self._remove_reaction(_ARROW_TO_BEGINNING)
                    continue
                else:
                    self.chunk_index = 0
                    await self.update_message()
                    await self._remove_reaction(_ARROW_TO_BEGINNING)

            elif str(reaction) == _ARROW_BACKWARD:
                if self.chunk_index == 0:
                    await self._remove_reaction(_ARROW_BACKWARD)
                    continue
                else:
                    self.chunk_index -= 1
                await self.update_message()
                await self._remove_reaction(_ARROW_BACKWARD)

            elif str(reaction) == _ARROW_FORWARD:
                if self.chunk_index == len(self.chunks) - 1:
                    await self._remove_reaction(_ARROW_FORWARD)
                    continue
                else:
                    self.chunk_index += 1
                await self.update_message()
                await self._remove_reaction(_ARROW_FORWARD)

            elif str(reaction) == _ARROW_TO_END:
                if self.chunk_index == len(self.chunks) - 1:
                    await self._remove_reaction(_ARROW_TO_END)
                    continue
                else:
                    self.chunk_index = len(self.chunks) - 1
                await self.update_message()
                await self._remove_reaction(_ARROW_TO_END)
