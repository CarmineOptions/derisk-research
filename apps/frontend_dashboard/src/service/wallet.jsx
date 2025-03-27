import { connect, disconnect, getSelectedConnectorWallet } from 'starknetkit';
import { InjectedConnector } from 'starknetkit/injected';
import { Provider } from 'starknet'; // Import Provider from starknet

// Token addresses for Mainnet
const ETH_ADDRESS_MAINNET = '0x49d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7';
const USDC_ADDRESS_MAINNET = '0x053c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8';

// Token addresses for Sepolia Testnet
const ETH_ADDRESS_TESTNET = '0x49d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7';
const USDC_ADDRESS_TESTNET = null; 

// Get available wallet connectors (ArgentX, Braavos)
export const getConnectors = () =>
  !localStorage.getItem('starknetLastConnectedWallet')
    ? [
        new InjectedConnector({ options: { id: 'argentX' } }),
        new InjectedConnector({ options: { id: 'braavos' } }),
      ]
    : [
        new InjectedConnector({
          options: { id: localStorage.getItem('starknetLastConnectedWallet') },
        }),
      ];

// Check for an existing wallet connection without prompting
export const getWallet = async () => {
  try {
    const connectedWallet = await getSelectedConnectorWallet();
    if (connectedWallet && connectedWallet.isConnected) {
      console.log('Found existing wallet:', connectedWallet.selectedAddress);
      return connectedWallet;
    }

    // Attempt to silently reconnect with 'neverAsk'
    console.log('No wallet found. Attempting to silently reconnect...');
    const { wallet } = await connect({
      connectors: getConnectors(),
      modalMode: 'neverAsk',
      modalTheme: 'dark',
    });

    if (!wallet) {
      console.log('No wallet to silently reconnect. Waiting for user to connect manually...');
      return null;
    }

    await wallet.enable();

    if (wallet.isConnected) {
      console.log('Silently reconnected wallet:', wallet.selectedAddress);
      return wallet;
    } else {
      console.log('No wallet connected. Waiting for user to connect manually...');
      return null;
    }
  } catch (error) {
    console.error('Error getting wallet:', error.message);
    throw error;
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
      console.log('Wallet connected:', wallet.selectedAddress);
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
    throw error; // Throw the error to be handled by the caller
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
    const isMainnet = chainId === '0x534e5f4d41494e';
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
    console.log('Wallet disconnected');
  } catch (error) {
    console.error('Error disconnecting wallet:', error.message);
    throw error;
  }
};