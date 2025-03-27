import React, { useState, useEffect } from 'react';
import { connectWallet, getWallet, getTokenBalances, disconnectWallet } from '../service/wallet';
import '../Dashboard.css';

function Dashboard() {
  const [walletAddress, setWalletAddress] = useState(null);
  const [balances, setBalances] = useState(null);
  const [network, setNetwork] = useState(null);
  const [error, setError] = useState(null);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);

  // Load wallet on page reload
  useEffect(() => {
    const loadWallet = async () => {
      try {
        setError(null); // Clear any previous errors
        const wallet = await getWallet();
        if (wallet && wallet.isConnected) {
          const address = wallet.selectedAddress;
          setWalletAddress(address);

          const { balances, network } = await getTokenBalances(address);
          setBalances(balances);
          setNetwork(network);
          console.log(`Balances loaded on page reload (${network}):`, balances);
        }
      } catch (error) {
        console.error('Failed to load wallet on page reload:', error);
        if (error.message.includes('Contract not found')) {
          setError(`Failed to fetch balances: Token contract not found on ${network === 'mainnet' ? 'Mainnet' : 'Sepolia Testnet'}. Please ensure the token addresses are correct for this network.`);
        } else {
          setError(`Failed to fetch balances: ${error.message}`);
        }
      }
    };

    loadWallet();
  }, []);

  const truncateAddress = (address) => {
    if (!address) return '';
    return `${address.slice(0, 6)}...${address.slice(-4)}`;
  };

  const handleConnectWallet = async () => {
    if (walletAddress) {
      setIsDropdownOpen(!isDropdownOpen);
      return;
    }

    try {
      setError(null);
      const wallet = await connectWallet('alwaysAsk');
      const address = wallet.selectedAddress;
      setWalletAddress(address);

      const { balances, network } = await getTokenBalances(address);
      setBalances(balances);
      setNetwork(network);
      console.log(`Balances (${network}):`, balances);
    } catch (error) {
      console.error('Failed to connect wallet or fetch balances:', error);
      if (error.message.includes('Contract not found')) {
        setError(`Failed to fetch balances: Token contract not found on ${network === 'mainnet' ? 'Mainnet' : 'Sepolia Testnet'}. Please ensure the token addresses are correct for this network.`);
      } else {
        setError(`Failed to fetch balances: ${error.message}`);
      }
    }
  };

  const handleDisconnect = async () => {
    try {
      await disconnectWallet();
      setWalletAddress(null);
      setBalances(null);
      setNetwork(null);
      setError(null);
      setIsDropdownOpen(false);
      console.log('Disconnected successfully');
    } catch (error) {
      console.error('Failed to disconnect wallet:', error);
      setError('Failed to disconnect wallet. Please try again.');
    }
  };

  return (
    <div>
      <h1>Dashboard</h1>
      <div className="wallet-button-container">
        <button onClick={handleConnectWallet} className="wallet-button">
          {walletAddress ? truncateAddress(walletAddress) : 'Connect Wallet'}
        </button>
        {isDropdownOpen && walletAddress && (
          <div className="dropdown">
            <button onClick={handleDisconnect}>Disconnect</button>
          </div>
        )}
      </div>
      {error && <p style={{ color: 'red' }}>{error}</p>}
      {balances && (
        <div>
          <h2>Balances on {network === 'mainnet' ? 'Mainnet' : 'Sepolia Testnet'}</h2>
          <pre>{JSON.stringify(balances, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}

export default Dashboard;