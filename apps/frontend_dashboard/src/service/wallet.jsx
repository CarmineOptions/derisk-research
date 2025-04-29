import { connect, disconnect, getSelectedConnectorWallet } from 'starknetkit';
import { InjectedConnector } from 'starknetkit/injected';
import { Provider } from 'starknet';

// Token addresses for Mainnet
const ETH_ADDRESS_MAINNET = '0x49d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7';
const USDC_ADDRESS_MAINNET = '0x053c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8';

// Token addresses for Sepolia Testnet
const ETH_ADDRESS_TESTNET = '0x49d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7';
const USDC_ADDRESS_TESTNET = null;

// Store additional wallet state in localStorage
const storeWalletState = (wallet) => {
  if (!wallet || !wallet.id) return;
  
  // Store wallet ID for reconnection
  localStorage.setItem('starknetLastConnectedWallet', wallet.id);
  
  // Store wallet address if available
  if (wallet.selectedAddress) {
    localStorage.setItem('starknetLastConnectedAddress', wallet.selectedAddress);
  }
  
  console.log('Stored wallet state in localStorage:', { id: wallet.id, address: wallet.selectedAddress });
};

// Get available wallet connectors (ArgentX, Braavos)
export const getConnectors = () => {
  const lastConnectedWallet = localStorage.getItem('starknetLastConnectedWallet');
  console.log('Retrieved last connected wallet from localStorage:', lastConnectedWallet);

  return !lastConnectedWallet
    ? [
        new InjectedConnector({ options: { id: 'argentX' } }),
        new InjectedConnector({ options: { id: 'braavos' } }),
      ]
    : [
        new InjectedConnector({
          options: { id: lastConnectedWallet },
        }),
      ];
};

// Get wallet with a unified approach that works for both Argent and Braavos
export const getWallet = async () => {
  try {
    // First check if we already have a connected wallet (fastest path)
    const connectedWallet = await getSelectedConnectorWallet();
    if (connectedWallet && connectedWallet.isConnected) {
      console.log('Found existing wallet connection:', connectedWallet);
      storeWalletState(connectedWallet);
      return connectedWallet;
    }

    // Get stored wallet ID and address
    const lastWalletId = localStorage.getItem('starknetLastConnectedWallet');
    
    if (!lastWalletId) {
      console.log('No wallet information stored. Manual connection required.');
      return null;
    }
    
    console.log(`Attempting to reconnect ${lastWalletId} wallet...`);
    
    // Unified approach that works for both wallet types
    const connector = new InjectedConnector({ options: { id: lastWalletId } });
    
    // For both wallet types, first try a standard connection
    try {
      const { wallet } = await connect({
        connectors: [connector],
        modalMode: 'alwaysAsk', // Works better for both wallets
        modalTheme: 'dark',
      });
      
      if (wallet && wallet.isConnected) {
        console.log('Wallet reconnected successfully:', wallet);
        storeWalletState(wallet);
        return wallet;
      }
      
      // If wallet exists but not connected, try to enable it
      if (wallet) {
        await wallet.enable();
        if (wallet.isConnected) {
          console.log('Wallet enabled successfully:', wallet);
          storeWalletState(wallet);
          return wallet;
        }
      }
    } catch (error) {
      console.log('Standard reconnection approach failed:', error.message);
      // Continue to fallback approach
    }
    
    // If we get here, standard approach failed - try wallet-specific approaches
    if (lastWalletId === 'argentX') {
      try {
        // For Argent, try with neverAsk mode which worked previously
        const { wallet } = await connect({
          connectors: [connector],
          modalMode: 'neverAsk',
          modalTheme: 'dark',
        });
        
        if (wallet) {
          await wallet.enable();
          if (wallet.isConnected) {
            console.log('ArgentX reconnected with neverAsk mode:', wallet);
            storeWalletState(wallet);
            return wallet;
          }
        }
      } catch (argentError) {
        console.log('ArgentX specific reconnection failed:', argentError.message);
      }
    } else if (lastWalletId === 'braavos') {
      // For Braavos, we'll use the delayed approach that worked before
      return new Promise((resolve) => {
        setTimeout(async () => {
          try {
            const { wallet } = await connect({
              connectors: [connector],
              modalMode: 'onlyIfNotConnected',
              modalTheme: 'dark',
            });
            
            if (wallet) {
              await wallet.enable();
              if (wallet.isConnected) {
                console.log('Braavos reconnected after delay:', wallet);
                storeWalletState(wallet);
                resolve(wallet);
                return;
              }
            }
            console.log('Braavos reconnection failed after delay');
            resolve(null);
          } catch (err) {
            console.log('Braavos reconnection error after delay:', err.message);
            resolve(null);
          }
        }, 500);
      });
    }
    
    console.log('All reconnection attempts failed. Manual connection required.');
    return null;
  } catch (error) {
    console.error('Error in getWallet:', error.message);
    return null;
  }
};

// Connect to wallet (initial connection)
export const connectWallet = async (modalMode = 'alwaysAsk') => {
  try {
    const { wallet } = await connect({
      connectors: getConnectors(),
      modalMode,
      modalTheme: 'dark',
    });

    if (!wallet) {
      throw new Error('Failed to connect to wallet');
    }

    await wallet.enable();

    if (wallet.isConnected) {
      console.log('Wallet connected:', wallet);
      storeWalletState(wallet);
      return wallet;
    } else {
      throw new Error('Wallet connection failed');
    }
  } catch (error) {
    console.error('Error connecting wallet:', error.message);
    throw error;
  }
};

// Fetch token balance for a given token address
export const getTokenBalance = async (wallet, walletAddress, tokenAddress) => {
  try {
    // Use the wallet's provider directly
    if (!wallet.provider) {
      throw new Error('Wallet provider not available');
    }

    const response = await wallet.provider.callContract({
      contractAddress: tokenAddress,
      entrypoint: 'balanceOf',
      calldata: [walletAddress],
    });

    const tokenDecimals = tokenAddress.includes('USDC') ? 6 : 18;
    const balance = BigInt(response.result[0]).toString();
    const readableBalance = (Number(balance) / 10 ** tokenDecimals).toFixed(4);
    return readableBalance;
  } catch (error) {
    console.error(`Error fetching balance for token ${tokenAddress}:`, error.message);
    throw error; 
  }
};

// Fetch all token balances and return as JSON
export const getTokenBalances = async (walletAddress) => {
  try {
    const wallet = await getWallet();
    if (!wallet) {
      throw new Error('No wallet connected. Please connect a wallet first.');
    }

    // Detect the network (mainnet or testnet)
    const chainId = await wallet.provider.getChainId();
    const isMainnet = chainId === '0x534e5f4d41494e'; // SN_MAIN (mainnet chain ID)
    const network = isMainnet ? 'mainnet' : 'sepolia';
    console.log(`Connected to network: ${network}`);

    // Select token addresses based on network
    const ETH_ADDRESS = isMainnet ? ETH_ADDRESS_MAINNET : ETH_ADDRESS_TESTNET;
    const USDC_ADDRESS = isMainnet ? USDC_ADDRESS_MAINNET : USDC_ADDRESS_TESTNET;

    const balances = {
      ETH: await getTokenBalance(wallet, walletAddress, ETH_ADDRESS),
    };

    // Only fetch USDC if the address is available for the network
    if (USDC_ADDRESS) {
      balances.USDC = await getTokenBalance(wallet, walletAddress, USDC_ADDRESS);
    } else {
      console.log('USDC address not available for this network. Skipping USDC balance fetch.');
    }

    return { balances, network };
  } catch (error) {
    console.error('Error fetching token balances:', error.message);
    throw error;
  }
};

// Disconnect wallet
export const disconnectWallet = async () => {
  try {
    await disconnect();
    localStorage.removeItem('starknetLastConnectedWallet');
    localStorage.removeItem('starknetLastConnectedAddress');
    console.log('Wallet disconnected and localStorage cleared');
  } catch (error) {
    console.error('Error disconnecting wallet:', error.message);
    throw error;
  }
};