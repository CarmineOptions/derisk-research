import React, { useState, useEffect } from 'react';
import { connectWallet, getWallet, getTokenBalances, disconnectWallet } from '../service/wallet';
import '../Dashboard.css';

function Dashboard() {
  const [walletAddress, setWalletAddress] = useState(null);
  const [balances, setBalances] = useState(null);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);

  // Load wallet on page reload
  useEffect(() => {
    const loadWallet = async () => {
      try {
        // Check localStorage for a saved wallet address
        const savedAddress = localStorage.getItem('walletAddress');
        if (savedAddress) {
          setWalletAddress(savedAddress);
        }

        const wallet = await getWallet();
        if (wallet && wallet.isConnected) {
          const address = wallet.selectedAddress;
          setWalletAddress(address);
          // Save the wallet address to localStorage
          localStorage.setItem('walletAddress', address);

          const balanceData = await getTokenBalances(address);
          setBalances(balanceData);
          console.log('Balances loaded on page reload:', balanceData);
        }
      } catch (error) {
        console.error('Failed to load wallet on page reload:', error);
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
      // Use 'alwaysAsk' to prompt the user when they manually click the button
      const wallet = await connectWallet('alwaysAsk');
      const address = wallet.selectedAddress;
      setWalletAddress(address);
      // Save the wallet address to localStorage
      localStorage.setItem('walletAddress', address);

      const balanceData = await getTokenBalances(address);
      setBalances(balanceData);
      console.log('Balances:', balanceData);
    } catch (error) {
      console.error('Failed to connect wallet or fetch balances:', error);
    }
  };

  const handleDisconnect = async () => {
    try {
      await disconnectWallet();
      setWalletAddress(null);
      setBalances(null);
      setIsDropdownOpen(false);
      // Clear the wallet address from localStorage
      localStorage.removeItem('walletAddress');
      console.log('Disconnected successfully');
    } catch (error) {
      console.error('Failed to disconnect wallet:', error);
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
      {balances && <pre>{JSON.stringify(balances, null, 2)}</pre>}
    </div>
  );
}

export default Dashboard;