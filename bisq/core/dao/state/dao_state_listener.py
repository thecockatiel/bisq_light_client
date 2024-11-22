class DaoStateListener:
    def on_new_block_height(self, block_height: int):
        pass

    def on_parse_block_chain_complete(self):
        pass

    # Called before on_parse_txs_complete_after_batch_processing in case batch processing is complete
    def on_parse_block_complete(self, block):
        pass

    def on_parse_block_complete_after_batch_processing(self, block):
        pass

    # Called after the parsing of a block is complete and we do not allow any change in the daoState until the next
    # block arrives.
    def on_dao_state_changed(self, block):
        pass
