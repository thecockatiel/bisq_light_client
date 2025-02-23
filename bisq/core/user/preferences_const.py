from bisq.core.user.block_chain_explorer import BlockChainExplorer

BTC_MAIN_NET_EXPLORERS = [
    BlockChainExplorer("mempool.space (@wiz)", "https://mempool.space/tx/", "https://mempool.space/address/"),
    BlockChainExplorer("mempool.space Tor V3", "http://mempoolhqx4isw62xs7abwphsq7ldayuidyx2v2oethdhhj6mlo2r6ad.onion/tx/", "http://mempoolhqx4isw62xs7abwphsq7ldayuidyx2v2oethdhhj6mlo2r6ad.onion/address/"),
    BlockChainExplorer("mempool.emzy.de (@emzy)", "https://mempool.emzy.de/tx/", "https://mempool.emzy.de/address/"),
    BlockChainExplorer("mempool.emzy.de Tor V3", "http://mempool4t6mypeemozyterviq3i5de4kpoua65r3qkn5i3kknu5l2cad.onion/tx/", "http://mempool4t6mypeemozyterviq3i5de4kpoua65r3qkn5i3kknu5l2cad.onion/address/"),
    BlockChainExplorer("mempool Tor V3 (@runbtc)", "http://runbtcx3wfygbq2wdde6qzjnpyrqn3gvbks7t5jdymmunxttdvvttpyd.onion/tx/", "http://runbtcx3wfygbq2wdde6qzjnpyrqn3gvbks7t5jdymmunxttdvvttpyd.onion/address/"),
    BlockChainExplorer("Blockstream.info", "https://blockstream.info/tx/", "https://blockstream.info/address/"),
    BlockChainExplorer("Blockstream.info Tor V3", "http://explorerzydxu5ecjrkwceayqybizmpjjznk5izmitf2modhcusuqlid.onion/tx/", "http://explorerzydxu5ecjrkwceayqybizmpjjznk5izmitf2modhcusuqlid.onion/address/"),
    BlockChainExplorer("OXT", "https://oxt.me/transaction/", "https://oxt.me/address/"),
    BlockChainExplorer("Bitaps", "https://bitaps.com/", "https://bitaps.com/"),
    BlockChainExplorer("Blockcypher", "https://live.blockcypher.com/btc/tx/", "https://live.blockcypher.com/btc/address/"),
    BlockChainExplorer("Tradeblock", "https://tradeblock.com/bitcoin/tx/", "https://tradeblock.com/bitcoin/address/"),
    BlockChainExplorer("Biteasy", "https://www.biteasy.com/transactions/", "https://www.biteasy.com/addresses/"),
    BlockChainExplorer("Blockonomics", "https://www.blockonomics.co/api/tx?txid=", "https://www.blockonomics.co/#/search?q="),
    BlockChainExplorer("Chainflyer", "http://chainflyer.bitflyer.jp/Transaction/", "http://chainflyer.bitflyer.jp/Address/"),
    BlockChainExplorer("Smartbit", "https://www.smartbit.com.au/tx/", "https://www.smartbit.com.au/address/"),
    BlockChainExplorer("SoChain. Wow.", "https://chain.so/tx/BTC/", "https://chain.so/address/BTC/"),
    BlockChainExplorer("Blockchain.info", "https://blockchain.info/tx/", "https://blockchain.info/address/"),
    BlockChainExplorer("Insight", "https://insight.bitpay.com/tx/", "https://insight.bitpay.com/address/"),
    BlockChainExplorer("Blockchair", "https://blockchair.com/bitcoin/transaction/", "https://blockchair.com/bitcoin/address/")
]

BTC_TEST_NET_EXPLORERS = [
    BlockChainExplorer("Blockstream.info", "https://blockstream.info/testnet/tx/", "https://blockstream.info/testnet/address/"),
    BlockChainExplorer("Blockstream.info Tor V3", "http://explorerzydxu5ecjrkwceayqybizmpjjznk5izmitf2modhcusuqlid.onion/testnet/tx/", "http://explorerzydxu5ecjrkwceayqybizmpjjznk5izmitf2modhcusuqlid.onion/testnet/address/"),
    BlockChainExplorer("Blockcypher", "https://live.blockcypher.com/btc-testnet/tx/", "https://live.blockcypher.com/btc-testnet/address/"),
    BlockChainExplorer("Blocktrail", "https://www.blocktrail.com/tBTC/tx/", "https://www.blocktrail.com/tBTC/address/"),
    BlockChainExplorer("Biteasy", "https://www.biteasy.com/testnet/transactions/", "https://www.biteasy.com/testnet/addresses/"),
    BlockChainExplorer("Smartbit", "https://testnet.smartbit.com.au/tx/", "https://testnet.smartbit.com.au/address/"),
    BlockChainExplorer("SoChain. Wow.", "https://chain.so/tx/BTCTEST/", "https://chain.so/address/BTCTEST/"),
    BlockChainExplorer("Blockchair", "https://blockchair.com/bitcoin/testnet/transaction/", "https://blockchair.com/bitcoin/testnet/address/")
]

BTC_DAO_TEST_NET_EXPLORERS = [
    BlockChainExplorer("BTC DAO-testnet explorer", "https://bisq.network/explorer/btc/dao_testnet/tx/", "https://bisq.network/explorer/btc/dao_testnet/address/")
]

BSQ_MAIN_NET_EXPLORERS = [
    BlockChainExplorer("mempool.bisq.services (@devinbileck)", "https://mempool.bisq.services/tx/", "https://mempool.bisq.services/address/")
]

XMR_TX_PROOF_SERVICES_CLEAR_NET = [
    "xmrchain.net"
]

XMR_TX_PROOF_SERVICES = [
    "xmrexplrthytnunr4jasr3vnjc6jo5idsyxzv74a7ep7dy7lwcv2eoyd.onion",     # @runbtc
    "nklwsomtuok6dhqqecp3a26xzgokfgmeuaplcdkaxehncg57yzarvbad.onion"      # @suddenwhipvapor
]

TX_BROADCAST_SERVICES_CLEAR_NET = [
    "https://mempool.space/api/tx",         # @wiz
    "https://mempool.emzy.de/api/tx"        # @emzy
]

TX_BROADCAST_SERVICES = [
    "http://mempoolhqx4isw62xs7abwphsq7ldayuidyx2v2oethdhhj6mlo2r6ad.onion/api/tx",     # @wiz
    "http://mempool4t6mypeemozyterviq3i5de4kpoua65r3qkn5i3kknu5l2cad.onion/api/tx",     # @emzy
    "http://runbtcx3wfygbq2wdde6qzjnpyrqn3gvbks7t5jdymmunxttdvvttpyd.onion/api/tx"      # @runbtc
]
    
USE_SYMMETRIC_SECURITY_DEPOSIT = True
CLEAR_DATA_AFTER_DAYS_INITIAL = 99999  # feature effectively disabled until user agrees to settings notification
CLEAR_DATA_AFTER_DAYS_DEFAULT = 60     # used when user has agreed to settings notification
INITIAL_TRADE_LIMIT = 10000000
