import { connect, disconnect, getSelectedConnectorWallet } from 'starknetkit';
import { InjectedConnector } from 'starknetkit/injected';

// Token addresses (you can add more as needed)
const ETH_ADDRESS = '0x49d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7';
const USDC_ADDRESS = '0x053c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8';

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
    const response = await wallet.provider.callContract({
      contractAddress: tokenAddress,
      entrypoint: 'balanceOf',
      calldata: [walletAddress],
    });

    const tokenDecimals = tokenAddress === USDC_ADDRESS ? 6 : 18;
    const balance = BigInt(response.result[0]).toString();
    const readableBalance = (Number(balance) / 10 ** tokenDecimals).toFixed(4);
    return readableBalance;
  } catch (error) {
    console.error(`Error fetching balance for token ${tokenAddress}:`, error);
    return '0';
  }
};

// Fetch all token balances and return as JSON
export const getTokenBalances = async (walletAddress) => {
  try {
    const wallet = await getWallet();
    if (!wallet) {
      throw new Error('No wallet connected. Please connect a wallet first.');
    }
    const balances = {
      ETH: await getTokenBalance(wallet, walletAddress, ETH_ADDRESS),
      USDC: await getTokenBalance(wallet, walletAddress, USDC_ADDRESS),
    };
    return balances;
  } catch (error) {
    console.error('Error fetching token balances:', error);
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