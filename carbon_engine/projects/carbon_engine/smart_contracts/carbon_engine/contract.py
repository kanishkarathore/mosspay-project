from algopy import ARC4Contract, String
from algopy.arc4 import abimethod


class CarbonEngine(ARC4Contract):
    @abimethod()
    def hello(self, name: String) -> String:
        return "MossPay Carbon Verified for: " + name
