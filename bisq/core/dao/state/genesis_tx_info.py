from bisq.common.config.config import CONFIG
from bitcoinj.base.coin import Coin

class GenesisTxInfo:
    """
    Encapsulate the genesis txId and height.
    As we don't persist those data we don't want to have it in the DaoState directly and moved it to a separate class.
    Using a field in DaoState would not work well as we want to support that the data can be overwritten by
    program arguments for development testing and therefore it is set in the constructor.
    """
    
    MAINNET_GENESIS_TX_ID = "4b5417ec5ab6112bedf539c3b4f5a806ed539542d8b717e1c4470aa3180edce5"
    MAINNET_GENESIS_BLOCK_HEIGHT = 571747  # 2019-04-15
    MAINNET_GENESIS_TOTAL_SUPPLY = Coin.parse_coin("3.65748")

    TESTNET_GENESIS_TX_ID = "f35b62930b16a680ba6bc8ba8fecc4f1db65c5635b5a4b4b0445544649acf4f6"
    TESTNET_GENESIS_BLOCK_HEIGHT = 1564395  # 2019-06-21
    TESTNET_GENESIS_TOTAL_SUPPLY = Coin.parse_coin("2.5")  # 2.5M BSQ / 2.50000000 BTC

    DAO_TESTNET_GENESIS_TX_ID = "cb316a186b9e88d1b8e1ce8dc79cc6a2080cc7bbc6df94f2be325d8253417af1"
    DAO_TESTNET_GENESIS_BLOCK_HEIGHT = 104  # 2019-02-19
    DAO_TESTNET_GENESIS_TOTAL_SUPPLY = Coin.parse_coin("2.5")  # 2.5M BSQ / 2.50000000 BTC

    DAO_BETANET_GENESIS_TX_ID = "0bd66d8ff26476b55dfaf2a5db0c659a5d8635566488244df25606db63a08bd9"
    DAO_BETANET_GENESIS_BLOCK_HEIGHT = 567405  # 2019-03-16
    DAO_BETANET_GENESIS_TOTAL_SUPPLY = Coin.parse_coin("0.49998644")  # 499 986.44 BSQ / 0.49998644 BTC

    DAO_REGTEST_GENESIS_TX_ID = "d594ad0c5de53e261b5784e5eb2acec8b807c45b74450401f488d36b8acf2e14"
    DAO_REGTEST_GENESIS_BLOCK_HEIGHT = 104  # 2019-03-26
    DAO_REGTEST_GENESIS_TOTAL_SUPPLY = Coin.parse_coin("2.5")  # 2.5M BSQ / 2.50000000 BTC

    REGTEST_GENESIS_TX_ID = "30af0050040befd8af25068cc697e418e09c2d8ebd8d411d2240591b9ec203cf"
    REGTEST_GENESIS_BLOCK_HEIGHT = 111
    REGTEST_GENESIS_TOTAL_SUPPLY = Coin.parse_coin("2.5")  # 2.5M BSQ / 2.50000000 BTC


    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Instance fields
    # ///////////////////////////////////////////////////////////////////////////////////////////
    
    # (JAVA IMPLEMENTATION COMMENTS:)
    
    # mainnet
    # this tx has a lot of outputs
    # https://blockchain.info/de/tx/ee921650ab3f978881b8fe291e0c025e0da2b7dc684003d7a03d9649dfee2e15
    # BLOCK_HEIGHT 411779
    # 411812 has 693 recursions
    # block 376078 has 2843 recursions and caused once a StackOverflowError, a second run worked. Took 1,2 sec.


    # BTC MAIN NET
    # new: --genesisBlockHeight=524717 --genesisTxId=81855816eca165f17f0668898faa8724a105196e90ffc4993f4cac980176674e
    #  private static final String DEFAULT_GENESIS_TX_ID = "e5c8313c4144d219b5f6b2dacf1d36f2d43a9039bb2fcd1bd57f8352a9c9809a";
    # private static final int DEFAULT_GENESIS_BLOCK_HEIGHT = 477865; // 2017-07-28


    # private static final String DEFAULT_GENESIS_TX_ID = "--";
    # private static final int DEFAULT_GENESIS_BLOCK_HEIGHT = 499000; // recursive test 137298, 499000 dec 2017


    def __init__(self, genesis_tx_id: str = "", genesis_block_height: int = -1, genesis_total_supply: int = -1):
        base_currency_network = CONFIG.base_currency_network
        is_mainnet = base_currency_network.is_mainnet()
        is_testnet = base_currency_network.is_testnet()
        is_dao_test_net = base_currency_network.is_dao_testnet()
        is_dao_beta_net = base_currency_network.is_dao_betanet()
        is_dao_reg_test = base_currency_network.is_dao_regtest()
        is_regtest = base_currency_network.is_regtest()

        if genesis_tx_id:
            self.genesis_tx_id = genesis_tx_id
        elif is_mainnet:
            self.genesis_tx_id = GenesisTxInfo.MAINNET_GENESIS_TX_ID
        elif is_testnet:
            self.genesis_tx_id = GenesisTxInfo.TESTNET_GENESIS_TX_ID
        elif is_dao_test_net:
            self.genesis_tx_id = GenesisTxInfo.DAO_TESTNET_GENESIS_TX_ID
        elif is_dao_beta_net:
            self.genesis_tx_id = GenesisTxInfo.DAO_BETANET_GENESIS_TX_ID
        elif is_dao_reg_test:
            self.genesis_tx_id = GenesisTxInfo.DAO_REGTEST_GENESIS_TX_ID
        elif is_regtest:
            self.genesis_tx_id = GenesisTxInfo.REGTEST_GENESIS_TX_ID
        else:
            self.genesis_tx_id = "genesisTxId is undefined"

        if genesis_block_height > -1:
            self.genesis_block_height = genesis_block_height
        elif is_mainnet:
            self.genesis_block_height = GenesisTxInfo.MAINNET_GENESIS_BLOCK_HEIGHT
        elif is_testnet:
            self.genesis_block_height = GenesisTxInfo.TESTNET_GENESIS_BLOCK_HEIGHT
        elif is_dao_test_net:
            self.genesis_block_height = GenesisTxInfo.DAO_TESTNET_GENESIS_BLOCK_HEIGHT
        elif is_dao_beta_net:
            self.genesis_block_height = GenesisTxInfo.DAO_BETANET_GENESIS_BLOCK_HEIGHT
        elif is_dao_reg_test:
            self.genesis_block_height = GenesisTxInfo.DAO_REGTEST_GENESIS_BLOCK_HEIGHT
        elif is_regtest:
            self.genesis_block_height = GenesisTxInfo.REGTEST_GENESIS_BLOCK_HEIGHT
        else:
            self.genesis_block_height = 0

        if genesis_total_supply > -1:
            self.genesis_total_supply = genesis_total_supply
        elif is_mainnet:
            self.genesis_total_supply = GenesisTxInfo.MAINNET_GENESIS_TOTAL_SUPPLY.value
        elif is_testnet:
            self.genesis_total_supply = GenesisTxInfo.TESTNET_GENESIS_TOTAL_SUPPLY.value
        elif is_dao_test_net:
            self.genesis_total_supply = GenesisTxInfo.DAO_TESTNET_GENESIS_TOTAL_SUPPLY.value
        elif is_dao_beta_net:
            self.genesis_total_supply = GenesisTxInfo.DAO_BETANET_GENESIS_TOTAL_SUPPLY.value
        elif is_dao_reg_test:
            self.genesis_total_supply = GenesisTxInfo.DAO_REGTEST_GENESIS_TOTAL_SUPPLY.value
        elif is_regtest:
            self.genesis_total_supply = GenesisTxInfo.REGTEST_GENESIS_TOTAL_SUPPLY.value
        else:
            self.genesis_total_supply = 0

