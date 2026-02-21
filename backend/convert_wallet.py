from eth_account import Account

# Enable mnemonic features
Account.enable_unaudited_hdwallet_features()

# Read the environment file
mnemonic = "horn common regular into equip slim vocal walk kidney glory genre dizzy"

acc = Account.from_mnemonic(mnemonic)
print("Address:", acc.address)
print("PrivateKey:", acc.key.hex())
