class classproperty(property):
    """~read-only class-level @property
    from https://stackoverflow.com/a/13624858 by denis-ryzhkov
    """

    def __get__(self, owner_self, owner_cls):
        return self.fget(owner_cls)
