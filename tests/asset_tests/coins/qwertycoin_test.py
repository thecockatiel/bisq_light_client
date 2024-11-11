import unittest
from bisq.asset.coins.qwertycoin import Qwertycoin 
from tests.asset_tests.abstract_asset_test import AbstractAssetTest
 
class QwertycoinTest(AbstractAssetTest):

    def __init__(self, methodName='runTest'):
        super().__init__(methodName, Qwertycoin())
    
    def test_valid_addresses(self):
        self.assert_valid_address("QWC1NStUeRB9hZiYH8sG5RAWEt7YycyB44YZnpZQBpgq4CLwmLw4vAk9tU3h7Td21NL9aMbLHxseDGKdEv3gRexo2QCodNEZWa")
        self.assert_valid_address("QWC1anUNJRo2HePBmenLFkGu8rnug4odGLCjHaCqAwMxboiZZS3Gv9ACLfn2zvcsGVcCc51eqZXB8Dot9X5qAt3F53F8BxjDrG")
        self.assert_valid_address("QWC1hgpbsxsPrpxH9H3wL771p4KdgS7vA369PQTiznHiCC3NjZxKJSmBtJPVCJBBUKE346FcPTsQ18W6fgiDzj762BHNgo2sir")
        self.assert_valid_address("QWC1YAvWpYBVs8XT2eSt2JV5iAJSdm8CwbQhDruuBeTzRNKSdtdK8Mn3WjaXQrFvjMMWWTf24x89p31mWppJN2Br9uiA5zdYQu")
        self.assert_valid_address("QWC1YzR91Zmcj7fpf1HRZhSfz6cgXbxqAVTjQTtrUV6Bfv1ysEzb78qgVojE7FuQWSRnVqSb3LyxP9nH2q4vWyo82Fonutfkzr")
        self.assert_valid_address("QWC1KYAwX6sRXK94HabKLCFNMjfC12KFC74cRjTgFtsD79VUBydTtMd3G2z4xLg2e1LKaXsTt3zkYibH3pBrAMjd5z5ConjRXn")
        self.assert_valid_address("QWC1ZgSyFwS3tUbmCRPGDBi224ynMZXgXCHxvQ5pEmtuZSCrmid4z1de1DWRjhZKRZXe4E5LYhtP6e7FmpN8R2MM2SHGFvg12z")
        self.assert_valid_address("QWC1W7223e83cBdseddQp461j49bhr7y4VHh8FTPs7qWArhpqBzNvrYR5QXyFtc3eRaoASo3QVhuT6ogAa6AHhgt4bVMUNpZGh")
        self.assert_valid_address("QWC1NgBcSwvXghUkEqGttNPSSmPEgEdknXELNLyTG444Fx3cKkV2oJ9iCwzySbps7y9BqqkWAKbkvdkA8FTspfdm29ScDzASK1")
        self.assert_valid_address("QWC1FVgbYqkafwnpW8KU2gKXLTKoraMXuEJ2c1yG6PNdesh6BA3Wq8d1mgRYqfsbCn53g5VLHuxyLT8CXnGRLxN64wHssuSa9D")

    def test_invalid_addresses(self):  
        self.assert_invalid_address("")
        self.assert_invalid_address("QW009s5NiYva6XS9bhhVc6jKYgXsH9wuHhZhWsqyAoPoWPUEiwEo9AZCDNbksvknyvZk73zwhHWSiXdgcDGLyhk5teEM7yxTgk")
        self.assert_invalid_address("WC115a2NPZy7Xe2WZt3nKMZBsBpgNdevnKfy6PLk99eCjYw5fWQ5nu4uM6LerRBvVKTJpdGp2acZ25X3QDPHc7ocTxz1WfN2Za")
        self.assert_invalid_address("34BQWC8imA1UH29uR6PHiGpcz9MYdnL3rku27gGeLosn5XuSedFC7jPBmzaB9DoxmDA5VUZa5hPv6PSe3tJH2MJhBktMEJXaZ8")
        self.assert_invalid_address("KWC45Ghz2JRTTrLh8Z4bm6QhzZxVbq7LPiKbgjjhHPNDvVXZAJLop91zRu9A7wJMjyrU89uF7QpZB5kHhniuGZ88MJv7jRZXNi")
        self.assert_invalid_address("ABc58FFmFEGcS52mTWmhAskQaKSSiX1BnHo8YcDjuhPdYBpWT9Q6ZCDz54k6cs3jPF2nk6desb1T6vRfHLfthiNf561qPct2SY")
        self.assert_invalid_address("2K267rMF5ve4nt2wTHYJ1pZ6j3o2YP5KDBnE7GDxnr6bpem9WcqeHzw9yKWXvtxYdpDXCBbLiX9nm97r4aEtnXq8YNb9WPn15f")
        self.assert_invalid_address("798Qr9sWTprQ2sH2y5PGpfV3RAnFxUsJYY2a2VQWCA9GjZ3MiyScD8VEh8ifWk4toYRCcbLZmRJw2dSsJBJAJ1Ava8WBzW7J12")
        self.assert_invalid_address("A2o85CQSLDNNKR4HGHwhtsxhm8jheYEvk6ngf44AhqCRWDV2XsaTHr6ittDuyfCjinAP1SzBqnVJfqNhYGDJLzxq4Y7FBVofXV")
        self.assert_invalid_address("QW9AeKW87bkao59oadmTXGf8Jv7sMYByPrKahRbnmZEmGzRgoxGRbWqmmXuPDW6jPJSUAdpZRZn6E5B9935LtWD5gHAPpZQA")


if __name__ == '__main__':
    unittest.main()