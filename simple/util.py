from math import ceil
import re
import unicodedata


class Pagination(object):

    def __init__(self, page, per_page, total_count):
        self.page = page
        self.per_page = per_page
        self.total_count = total_count

    @property
    def pages(self):
        return int(ceil(self.total_count / float(self.per_page)))

    @property
    def has_prev(self):
        return self.page > 1

    @property
    def has_next(self):
        return self.page < self.pages

    @property
    def previous(self):
        return self.page - 1

    @property
    def next(self):
        return self.page + 1

    @property
    def offset(self):
        return (self.page - 1) * self.per_page

    def iter_pages(self):
        return range(1, self.pages + 1)


# https://stackoverflow.com/questions/6657820/python-convert-an-iterable-to-a-stream
class iter_to_stream(object):
    def __init__(self, iterable):
        self.buffered = b""
        self.iter = iter(iterable)

    def read(self, size):
        result = b""
        while size > 0:
            data = self.buffered or next(self.iter, None)
            self.buffered = ""
            if data is None:
                break
            size -= len(data)
            if size < 0:
                data, self.buffered = data[:size], data[size:]
            result += data
        return result


def slugify(string):

    """
    Slugify a unicode string.

    Example:

        >>> slugify(u"Héllø Wörld")
        u"hello-world"

    """
    sub = unicodedata.normalize('NFKD', string)
    return re.sub('[-\\s]+', '-', re.sub('[^\\w\\s-]', '', sub)
                  .strip()
                  .lower())