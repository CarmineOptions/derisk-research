import { connect, disconnect, getSelectedConnectorWallet } from 'starknetkit';
import { InjectedConnector } from 'starknetkit/injected';

// Token addresses (you can add more as needed)
const ETH_ADDRESS = '0x...'; 
const USDC_ADDRESS = '0x...'; 

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

// Connect to wallet
export const connectWallet = async () => {
  try {
    const { wallet } = await connect({
      connectors: getConnectors(),
      modalMode: 'alwaysAsk',
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
    const wallet = await connectWallet();
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