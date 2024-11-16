import unittest
from unittest.mock import Mock, patch
from typing import List, Optional
from bisq.core.network.p2p.node_address import NodeAddress
from bisq.core.network.p2p.seed.default_seed_node_repository import DefaultSeedNodeRepository
from bisq.common.config.config import Config

class TestDefaultSeedNodeRepository(unittest.TestCase):
    def setUp(self):
        self.config = Mock(spec=Config)
        self.config.seed_nodes = []
        self.config.filter_provided_seed_nodes = []
        self.config.banned_seed_nodes = []
        self.repo = DefaultSeedNodeRepository(self.config)

    def test_init(self):
        self.assertEqual(len(self.repo.cache), 0)
        self.assertEqual(self.repo.config, self.config)

    @patch('bisq.core.network.p2p.seed.default_seed_node_repository.resource_readlines')
    def test_reload_with_config_seed_nodes(self, mock_resource_readlines):
        # Given
        self.config.seed_nodes = ['node1.onion:8000', 'node2.onion:8000']
        
        # When
        self.repo.reload()
        
        # Then
        self.assertEqual(len(self.repo.cache), 2)
        mock_resource_readlines.assert_not_called()

    @patch('bisq.core.network.p2p.seed.default_seed_node_repository.resource_readlines')
    def test_reload_from_property_file(self, mock_resource_readlines):
        # Given
        mock_resource_readlines.return_value = [
            'node1.onion:8000',
            'localhost:8000',
            'bisq-seednode-1:8000'
        ]
        
        # When
        self.repo.reload()
        
        # Then
        self.assertEqual(len(self.repo.cache), 3)

    @patch('bisq.core.network.p2p.seed.default_seed_node_repository.resource_readlines')
    def test_reload_with_banned_nodes(self, mock_resource_readlines):
        # Given
        mock_resource_readlines.return_value = ['node1.onion:8000', 'node2.onion:8000']
        self.config.banned_seed_nodes = ['node1.onion:8000']
        
        # When
        self.repo.reload()
        
        # Then
        self.assertEqual(len(self.repo.cache), 1)

    def test_get_seed_node_addresses_empty_cache(self):
        # Given
        self.repo.cache = set()
        
        # When
        with patch.object(self.repo, 'reload') as mock_reload:
            self.repo.get_seed_node_addresses()
            
            # Then
            mock_reload.assert_called_once()

    def test_is_seed_node(self):
        # Given
        node = NodeAddress.from_full_address('node1.onion:8000')
        self.repo.cache = {node}
        
        # Then
        self.assertTrue(self.repo.is_seed_node(node))
        self.assertFalse(self.repo.is_seed_node(NodeAddress.from_full_address('node2.onion:8000')))

    def test_get_node_address_valid(self):
        # Given
        address = 'node1.onion:8000'
        
        # When
        result = self.repo.get_node_address(address)
        
        # Then
        self.assertIsNotNone(result)
        self.assertEqual(str(result), address)

    def test_get_node_address_invalid(self):
        # Given
        address = 'invalid:address'
        
        # When
        result = self.repo.get_node_address(address)
        
        # Then
        self.assertIsNone(result)

    @patch('bisq.core.network.p2p.seed.default_seed_node_repository.resource_readlines')
    def test_get_seed_node_addresses_from_property_file(self, mock_resource_readlines):
        # Given
        mock_resource_readlines.return_value = [
            'node1.onion:8000',
            'invalid line',
            'localhost:8000',
            'bisq-seednode-1:8000'
        ]
        
        # When
        result = self.repo.get_seed_node_addresses_from_property_file('btc_mainnet')
        
        # Then
        self.assertEqual(len(result), 3)
        self.assertTrue(all(isinstance(addr, NodeAddress) for addr in result))

    @patch('bisq.core.network.p2p.seed.default_seed_node_repository.resource_readlines')
    def test_get_seed_node_addresses_from_property_file_empty(self, mock_resource_readlines):
        # Given
        mock_resource_readlines.return_value = []
        
        # When
        result = self.repo.get_seed_node_addresses_from_property_file('btc_mainnet')
        
        # Then
        self.assertEqual(len(result), 0)

if __name__ == '__main__':
    unittest.main()