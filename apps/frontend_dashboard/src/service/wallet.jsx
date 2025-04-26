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

// Enhanced wallet reconnection with improved fallbacks for different wallet behaviors
export const getWallet = async () => {
  try {
    // First, check for an already connected wallet (fastest path)
    const connectedWallet = await getSelectedConnectorWallet();
    if (connectedWallet && connectedWallet.isConnected) {
      console.log('Found existing wallet connection:', connectedWallet);
      storeWalletState(connectedWallet);
      return connectedWallet;
    }

    // Get stored wallet ID and address
    const lastWalletId = localStorage.getItem('starknetLastConnectedWallet');
    const lastWalletAddress = localStorage.getItem('starknetLastConnectedAddress');
    
    console.log('Attempting to reconnect wallet from stored state:', { id: lastWalletId, address: lastWalletAddress });

    // If we don't have stored wallet info, we can't reconnect
    if (!lastWalletId) {
      console.log('No wallet information stored. Manual connection required.');
      return null;
    }

    // Try silent reconnection first (works well with ArgentX)
    try {
      console.log(`Attempting silent reconnection for ${lastWalletId}...`);
      const { wallet } = await connect({
        connectors: [new InjectedConnector({ options: { id: lastWalletId } })],
        modalMode: 'neverAsk',
        modalTheme: 'dark',
      });

      if (wallet && wallet.isConnected) {
        console.log('Silent reconnection successful:', wallet);
        storeWalletState(wallet);
        return wallet;
      }
    } catch (silentError) {
      console.log('Silent reconnection failed:', silentError.message);
      // Continue to fallback methods - don't throw here
    }

    // For Braavos, we need a special approach since it may not support silent reconnection
    if (lastWalletId === 'braavos') {
      console.log('Using Braavos-specific reconnection approach...');
      
      // For Braavos, we'll try a different reconnection approach with a small timeout
      // to allow the wallet extension to initialize properly
      return new Promise((resolve) => {
        setTimeout(async () => {
          try {
            const { wallet } = await connect({
              connectors: [new InjectedConnector({ options: { id: 'braavos' } })],
              modalMode: 'onlyIfNotConnected', // This mode might work better with Braavos
              modalTheme: 'dark',
            });
            
            if (wallet && await wallet.enable()) {
              console.log('Braavos reconnection successful after delay:', wallet);
              storeWalletState(wallet);
              resolve(wallet);
            } else {
              console.log('Braavos reconnection failed after delay');
              resolve(null);
            }
          } catch (err) {
            console.log('Braavos reconnection error after delay:', err.message);
            resolve(null);
          }
        }, 500); // Small delay to allow wallet extension to initialize
      });
    }

    // At this point, we couldn't reconnect silently
    console.log('All reconnection attempts failed. Waiting for manual connection.');
    return null;
  } catch (error) {
    console.error('Error in getWallet:', error.message);
    return null; // Return null instead of throwing to prevent blocking UI
  }
};

// Connect to wallet with configurable modal mode
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