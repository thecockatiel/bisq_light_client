# this file is taken from babel library and modified to remove the dependency on babel library
# as we only need the default locale detection

import os


def default_locale(category: str = None):
    """Returns the system default locale for a given category, based on
    environment variables.

    >>> for name in ['LANGUAGE', 'LC_ALL', 'LC_CTYPE']:
    ...     os.environ[name] = ''
    >>> os.environ['LANG'] = 'fr_FR.UTF-8'
    >>> default_locale('LC_MESSAGES')
    'fr_FR'

    The "C" or "POSIX" pseudo-locales are treated as aliases for the
    "en_US_POSIX" locale:

    >>> os.environ['LC_MESSAGES'] = 'POSIX'
    >>> default_locale('LC_MESSAGES')
    'en_US_POSIX'

    The following fallbacks to the variable are always considered:

    - ``LANGUAGE``
    - ``LC_ALL``
    - ``LC_CTYPE``
    - ``LANG``

    :param category: one of the ``LC_XXX`` environment variable names
    :param aliases: a dictionary of aliases for locale identifiers
    """
    varnames = (category, 'LANGUAGE', 'LC_ALL', 'LC_CTYPE', 'LANG')
    for name in filter(None, varnames):
        locale = os.getenv(name)
        if locale:
            if name == 'LANGUAGE' and ':' in locale:
                # the LANGUAGE variable may contain a colon-separated list of
                # language codes; we just pick the language on the list
                locale = locale.split(':')[0]
            if locale.split('.')[0] in ('C', 'POSIX'):
                locale = 'en_US'
            try:
                return parse_locale(locale)
            except ValueError:
                pass


def parse_locale(identifier: str, sep='_'):
    """Parse a locale identifier into a tuple of the form ``(language,
    territory, script, variant)``.

    >>> parse_locale('zh_CN')
    ('zh', 'CN', None, None)
    >>> parse_locale('zh_Hans_CN')
    ('zh', 'CN', 'Hans', None)
    >>> parse_locale('ca_es_valencia')
    ('ca', 'ES', None, 'VALENCIA')
    >>> parse_locale('en_150')
    ('en', '150', None, None)
    >>> parse_locale('en_us_posix')
    ('en', 'US', None, 'POSIX')

    The default component separator is "_", but a different separator can be
    specified using the `sep` parameter:

    >>> parse_locale('zh-CN', sep='-')
    ('zh', 'CN', None, None)

    If the identifier cannot be parsed into a locale, a `ValueError` exception
    is raised:

    >>> parse_locale('not_a_LOCALE_String')
    Traceback (most recent call last):
      ...
    ValueError: 'not_a_LOCALE_String' is not a valid locale identifier

    Encoding information and locale modifiers are removed from the identifier:

    >>> parse_locale('it_IT@euro')
    ('it', 'IT', None, None)
    >>> parse_locale('en_US.UTF-8')
    ('en', 'US', None, None)
    >>> parse_locale('de_DE.iso885915@euro')
    ('de', 'DE', None, None)

    See :rfc:`4646` for more information.

    :param identifier: the locale identifier string
    :param sep: character that separates the different components of the locale
                identifier
    :raise `ValueError`: if the string does not appear to be a valid locale
                         identifier
    """
    if '.' in identifier:
        # this is probably the charset/encoding, which we don't care about
        identifier = identifier.split('.', 1)[0]
    if '@' in identifier:
        # this is a locale modifier such as @euro, which we don't care about
        # either
        identifier = identifier.split('@', 1)[0]

    parts = identifier.split(sep)
    lang = parts.pop(0).lower()
    if not lang.isalpha():
        raise ValueError('expected only letters, got %r' % lang)

    script = territory = variant = None
    if parts:
        if len(parts[0]) == 4 and parts[0].isalpha():
            script = parts.pop(0).title()

    if parts:
        if len(parts[0]) == 2 and parts[0].isalpha():
            territory = parts.pop(0).upper()
        elif len(parts[0]) == 3 and parts[0].isdigit():
            territory = parts.pop(0)

    if parts:
        if len(parts[0]) == 4 and parts[0][0].isdigit() or \
                len(parts[0]) >= 5 and parts[0][0].isalpha():
            variant = parts.pop().upper()

    if parts:
        raise ValueError('%r is not a valid locale identifier' % identifier)

    return lang, territory, script, variant
