import React, { useState, useEffect, useRef } from 'react';
import { connectWallet, getWallet, getTokenBalances, disconnectWallet } from '../service/wallet';
import '../Dashboard.css';
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/dashboard')({  component: Dashboard,
})

function Dashboard() {
  const [walletAddress, setWalletAddress] = useState(null);
  const [balances, setBalances] = useState(null);
  const [network, setNetwork] = useState(null);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const reconnectAttempted = useRef(false);

  
  useEffect(() => {
    
    const cachedAddress = localStorage.getItem('starknetLastConnectedAddress');
    if (cachedAddress && !walletAddress) {
      setWalletAddress(cachedAddress);
    }
  }, [walletAddress]);

  // Load wallet on page reload
  useEffect(() => {
    // Avoid duplicate reconnection attempts
    if (reconnectAttempted.current) return;
    reconnectAttempted.current = true;

    const loadWallet = async () => {
      setIsLoading(true);
      setError(null); // Clear any previous errors

      try {
        console.log('Attempting to reconnect wallet...');
        const wallet = await getWallet();
        
        if (wallet && wallet.isConnected) {
          const address = wallet.selectedAddress;
          setWalletAddress(address);
          console.log('Wallet reconnected successfully:', address);

         
          try {
            const { balances, network } = await getTokenBalances(address);
            setBalances(balances);
            setNetwork(network);
            console.log(`Balances loaded on page reload (${network}):`, balances);
          } catch (balanceError) {
            console.error('Failed to fetch balances:', balanceError);
            
            if (balanceError.message.includes('Contract not found')) {
              setError(`Failed to fetch balances: Token contract not found. Please ensure the token addresses are correct for this network.`);
            } else {
              setError(`Failed to fetch balances: ${balanceError.message}`);
            }
          }
        } else {
          console.log('No active wallet connection detected.');
          
          const cachedAddress = localStorage.getItem('starknetLastConnectedAddress');
          if (cachedAddress && !walletAddress) {
            console.log('Using cached address while waiting for reconnection:', cachedAddress);
            setWalletAddress(cachedAddress);
            setError('Waiting for wallet connection...');
          }
        }
      } catch (error) {
        console.error('Failed to load wallet on page reload:', error);
        setError(`Failed to reconnect wallet: ${error.message}`);
      } finally {
        setIsLoading(false);
      }
    };

    loadWallet();
  }, []); // Empty dependency array to run only on mount

  const truncateAddress = (address) => {
    if (!address) return '';
    return `${address.slice(0, 6)}...${address.slice(-4)}`;
  };

  const handleConnectWallet = async () => {
    if (walletAddress && isDropdownOpen) {
      setIsDropdownOpen(false);
      return;
    }

    if (walletAddress) {
      setIsDropdownOpen(true);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const wallet = await connectWallet('alwaysAsk');
      const address = wallet.selectedAddress;
      setWalletAddress(address);

      const { balances, network } = await getTokenBalances(address);
      setBalances(balances);
      setNetwork(network);
      setError(null);
      console.log(`Balances (${network}):`, balances);
    } catch (error) {
      console.error('Failed to connect wallet or fetch balances:', error);
      if (error.message.includes('Contract not found')) {
        setError(`Failed to fetch balances: Token contract not found. Please ensure the token addresses are correct for this network.`);
      } else {
        setError(`Failed to connect wallet: ${error.message}`);
      }
    } finally {
      setIsLoading(false);
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
        <button onClick={handleConnectWallet} className="wallet-button" disabled={isLoading}>
          {isLoading ? 'Connecting...' : walletAddress ? truncateAddress(walletAddress) : 'Connect Wallet'}
        </button>
        {isDropdownOpen && walletAddress && (
          <div className="dropdown">
            <button onClick={handleDisconnect}>Disconnect</button>
          </div>
        )}
      </div>
      {error && <p style={{ color: 'red' }}>{error}</p>}
      {isLoading && <p>Loading balances...</p>}
      {balances && !isLoading && (
        <div>
          <h2>Balances on {network === 'mainnet' ? 'Mainnet' : 'Sepolia Testnet'}</h2>
          <pre>{JSON.stringify(balances, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}

export default Dashboard;
