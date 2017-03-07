import unittest
import argParseWrapper
import configWrapper

if __name__ == "__main__":
	cfg = configWrapper.load_configuration()
	print argParseWrapper.return_args(cfg.args)