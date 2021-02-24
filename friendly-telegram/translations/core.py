#    Friendly Telegram (telegram userbot)
#    Copyright (C) 2018-2019 The Authors

#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.

#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.

import logging
import json
import telethon
from telethon.tl.types import MessageEntityHashtag

from babel import negotiate_locale

logger = logging.getLogger(__name__)


MAGIC = "#ftgtrnsl1"


class Translator:
    def __init__(self, packs, languages=["en"]):
        self._packs = packs
        self._languages = languages

    async def init(self, client):
        self._data = {}
        for pack in self._packs:
            try:
                [message] = await client.get_messages(pack, 1)
            except (ValueError, telethon.errors.rpcerrorlist.ChannelPrivateError):
                # There is no message with matching magic
                logger.warning("No translation pack found for %d", pack, exc_info=True)
                continue
            if not message.document:
                logger.info("Last message in translation pack %d has no document")
            found = False
            for ent in filter(lambda x: isinstance(x, MessageEntityHashtag), message.entities or []):
                if message.message[ent.offset:ent.offset + ent.length] == MAGIC:
                    logger.debug("Got translation message")
                    found = True
                    break
            if not found:
                logger.info("Didn't find translation hashtags")
                continue
            try:
                ndata = json.loads((await message.download_media(bytes)).decode("utf-8"))
            except (json.decoder.JSONDecodeError, UnicodeDecodeError):
                logger.exception("Unable to decode %s", pack, exc_info=True)
                continue
            try:
                self._data.setdefault(ndata["language"], {}).update(ndata["data"])
            except KeyError:
                logger.exception("Translation pack follows wrong format")

    def set_preferred_languages(self, languages):
        self._languages = languages

    def getkey(self, key):
        locales = []
        for locale, strings in self._data.items():
            if key in strings:
                locales += [locale]
        locale = negotiate_locale(self._languages, locales)
        return self._data.get(locale, {}).get(key, False)

    def gettext(self, english_text):
        return self.getkey(english_text) or english_text
