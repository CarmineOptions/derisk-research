import React, { useState } from 'react';
import { connectWallet, getTokenBalances, disconnectWallet } from '../service/wallet';
import '../Dashboard.css';

function Dashboard() {
  const [walletAddress, setWalletAddress] = useState(null);
  const [balances, setBalances] = useState(null);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);

  
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
      const wallet = await connectWallet();
      const address = wallet.selectedAddress;
      setWalletAddress(address);

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
      {balances && (
        <pre>{JSON.stringify(balances, null, 2)}</pre>
      )}
    </div>
  );
}

export default Dashboard;