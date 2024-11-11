def alt_coin_account_disclaimer(message: str):
    """
    When a new PaymentAccount is created for given asset, this annotation tells UI to show user a disclaimer message
    with requirements needed to be fulfilled when conducting trade given payment method.
    
    I.e. in case of Monero user must use official Monero GUI wallet or Monero CLI wallet with certain options enabled,
    user needs to keep tx private key, tx hash, recipient's address, etc.
    
    Args:
        message (str): Translation key of the message to show, i.e. "account.altcoin.popup.xmr.msg"
    """
    def decorator(cls):
        # Store the disclaimer message as a class attribute
        setattr(cls, '_disclaimer_message', message)
        return cls
    return decorator
