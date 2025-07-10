import React, { useState, useEffect, useRef } from 'react';
import { connectWallet, getWallet, getTokenBalances, disconnectWallet } from '../service/wallet';
import '../Dashboard.css';
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/Dashboard')({
  component: Dashboard,
})

function Dashboard() {
  const [walletAddress, setWalletAddress] = useState(null);
  const [balances, setBalances] = useState(null);
  const [network, setNetwork] = useState(null);
  const [error, setError] = useState(null);
  const [history, setHistory] = useState(null);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const [isLoadingWallet, setIsLoadingWallet] = useState(false);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const reconnectAttempted = useRef(false);

  // Helper to get localStorage key for a wallet
  const getHistoryCacheKey = (address) => `dashboardHistory_${address}`;

  // Load history: first from cache, then fetch in background
  useEffect(() => {
    if (!walletAddress) return;

    // 1. Try to load from cache
    const cacheKey = getHistoryCacheKey(walletAddress);
    const cached = localStorage.getItem(cacheKey);
    if (cached) {
      try {
        const parsed = JSON.parse(cached);
        setHistory(parsed);
      } catch (e) {
        // Corrupted cache, ignore
        setHistory(null);
      }
    } else {
      setHistory(null); // No cache, clear
    }

    // 2. Always fetch in background
    let cancelled = false;
    const fetchHistory = async () => {
      setIsLoadingHistory(true);
      try {
        const response = await fetch(`/api/history?wallet_id=${walletAddress}`);
        if (response.status === 200) {
          const freshHistory = await response.json();
          if (!cancelled) {
            setHistory(freshHistory || null);
            // Update cache
            localStorage.setItem(cacheKey, JSON.stringify(freshHistory || []));
          }
        }
      } catch (e) {
        // Optionally handle fetch error
      }
      if (!cancelled) setIsLoadingHistory(false);
    };
    fetchHistory();
    return () => { cancelled = true; };
  }, [walletAddress]);

  useEffect(() => {
    if (!walletAddress) {
      const cachedAddress = localStorage.getItem('starknetLastConnectedAddress') || '0x5105649f42252f79109356e1c8765b7dcdb9bf4a6a68534e7fc962421c7efd2';
      if (cachedAddress)
        setWalletAddress(cachedAddress);
    }

    if (walletAddress) {
      loadHistory();
    }
  }, [walletAddress]);

  const loadHistory = async () => {
    try {
      setIsLoadingHistory(true);
      const response = await fetch(`/api/history?wallet_id=${walletAddress}`);
      if (response.status === 200) {
        const history = await response.json();
        setHistory(history || null);
      }
    } catch (e) {

    }
    setIsLoadingHistory(false);
  };

  // Load wallet on page reload
  useEffect(() => {
    // Avoid duplicate reconnection attempts
    if (reconnectAttempted.current) return;
    reconnectAttempted.current = true;

    const loadWallet = async () => {
      setIsLoadingWallet(true);
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
        setIsLoadingWallet(false);
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

    setIsLoadingWallet(true);
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
      setIsLoadingWallet(false);
    }
  };

  const handleDisconnect = async () => {
    try {
      await disconnectWallet();
      // Clear wallet and history
      if (walletAddress) {
        const cacheKey = getHistoryCacheKey(walletAddress);
        localStorage.removeItem(cacheKey);
      }
      setWalletAddress(null);
      setBalances(null);
      setNetwork(null);
      setError(null);
      setIsDropdownOpen(false);
      setHistory(null);
      console.log('Disconnected successfully');
    } catch (error) {
      console.error('Failed to disconnect wallet:', error);
      setError('Failed to disconnect wallet. Please try again.');
    }
  };

  useEffect(() => {
    const BOT_NAME = 'derisk_afmsdlknfsda_bot';

    window.onTelegramAuth = onTelegramAuth;
    const script = document.createElement('script');
    script.src = "https://telegram.org/js/telegram-widget.js?22";
    script.setAttribute('data-telegram-login', BOT_NAME);
    script.setAttribute('data-size', 'large');
    script.setAttribute('data-onauth', "onTelegramAuth(user)");
    script.setAttribute('data-request-access', 'write');
    script.async = true;
    document.getElementById('tg-login').appendChild(script);

    return () => {
      document.getElementById('tg-login').removeChild(script);
    }
  }, []);

  async function onTelegramAuth(user) {
    console.log(user);
    try {
      const response = await fetch(`/api/auth/telegram-oauth`, {
        method: 'POST',
        body: user
      });
      if (response.status === 200) {
      }
    } catch (e) {

    }
  }


  return (
    <div className='w-[100vw]'>
      <div className="wallet-button-container">
        <button onClick={handleConnectWallet} className="wallet-button" disabled={isLoadingWallet}>
          {isLoadingWallet ? 'Connecting...' : walletAddress ? truncateAddress(walletAddress) : 'Connect Wallet'}
        </button>
        {isDropdownOpen && walletAddress && (
          <div className="dropdown">
            <button onClick={handleDisconnect}>Disconnect</button>
          </div>
        )}
      </div>
      <div id="tg-login" className='flex justify-center'></div>
      {/* TODO hide on prod */}
      <button onClick={() => onTelegramAuth(JSON.stringify({ 'a': 'a' }))}>Telegram dev oauth</button>
      <h1>Dashboard</h1>
      <div className="p-4 mx-auto">
        <h2 className="text-2xl font-bold mb-4">Trade History</h2>
        <div className="overflow-x-auto rounded-lg shadow-md text-black">
          {!isLoadingHistory && (
            <table className="min-w-full bg-white border border-gray-200">
              <thead className="bg-gray-100 text-gray-700 text-sm font-semibold">
                <tr>
                  <th className="px-4 py-3 text-left">Token</th>
                  <th className="px-4 py-3 text-left">Date</th>
                  <th className="px-4 py-3 text-right">Price</th>
                  <th className="px-4 py-3 text-right">Amount</th>
                  <th className="px-4 py-3 text-center">Type</th>
                </tr>
              </thead>
              <tbody>
                {history?.map((trade, index) => (
                  <tr
                    key={index}
                    className="border-t border-gray-200 hover:bg-gray-200"
                  >
                    <td className="px-4 py-2 text-start">{trade.token}</td>
                    <td className="px-4 py-2 text-start">
                      {new Date(trade.timestamp).toLocaleString()}
                    </td>
                    <td className="px-4 py-2 text-right">
                      {/* ${trade.price.toFixed(2)} */}
                    </td>
                    <td className="px-4 py-2 text-right">{trade.amount}</td>
                    <td
                      className={`px-4 py-2 text-center font-semibold ${trade.is_sell ? "text-red-600" : "text-green-600"
                        }`}
                    >
                      {trade.is_sell ? "Sell" : "Buy"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          {isLoadingHistory && (<div>Fetching data...</div>)}

        </div>
      </div>
      {error && <p style={{ color: 'red' }}>{error}</p>}
      {isLoadingWallet && <p>Loading balances...</p>}
      {balances && !isLoadingWallet && (
        <div>
          <h2>Balances on {network === 'mainnet' ? 'Mainnet' : 'Sepolia Testnet'}</h2>
          <pre>{JSON.stringify(balances, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}

export default Dashboard;
