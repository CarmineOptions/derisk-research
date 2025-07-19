import { Link } from "@tanstack/react-router";
import { useEffect, useRef, useState } from "react";
import { connectWallet, disconnectWallet, getTokenBalances, getWallet } from "../service/wallet";
import { useAppContext } from "../AppContext";

const Header = () => {
    const { walletAddress, setWalletAddress } = useAppContext();

    // '0x5105649f42252f79109356e1c8765b7dcdb9bf4a6a68534e7fc962421c7efd2'
    const [balances, setBalances] = useState(null);
    const [network, setNetwork] = useState(null);
    const [error, setError] = useState<string | null>(null);
    const [isLoadingWallet, setIsLoadingWallet] = useState(false);
    const [isDropdownOpen, setIsDropdownOpen] = useState(false);
    const reconnectAttempted = useRef(false);

    useEffect(() => {
        if (!walletAddress) {
            const cachedAddress = localStorage.getItem('starknetLastConnectedAddress');
            if (cachedAddress)
                setWalletAddress(cachedAddress);
        }
    }, [walletAddress]);


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


                    // try {
                    //     const { balances, network } = await getTokenBalances(address);
                    //     setBalances(balances);
                    //     setNetwork(network);
                    //     console.log(`Balances loaded on page reload (${network}):`, balances);
                    // } catch (balanceError) {
                    //     console.error('Failed to fetch balances:', balanceError);

                    //     if (balanceError.message.includes('Contract not found')) {
                    //         setError(`Failed to fetch balances: Token contract not found. Please ensure the token addresses are correct for this network.`);
                    //     } else {
                    //         setError(`Failed to fetch balances: ${balanceError.message}`);
                    //     }
                    // }
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
    }, []);


    const truncateAddress = (address: string) => {
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

            // const { balances, network } = await getTokenBalances(address);
            // setBalances(balances);
            // setNetwork(network);
            // setError(null);
            // console.log(`Balances (${network}):`, balances);
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
            setWalletAddress(undefined);
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
        <header className="grid place-items-center mt-8 mb-12  mx-auto z-50 ">
            <nav className="flex items-center justify-between h-[5.5rem] w-full lg:w-[70rem] rounded-2xl shadow-carmine px-6 py-5">
                <div className="flex justify-center items-center gap-8">
                    <div>
                        <a href="/" className="no-underline">
                            <img
                                src="/static/Carmine_logo.svg"
                                alt="Carmine Logo"
                            />
                        </a>
                    </div>
                    <div className="hidden lg:flex space-between justify-center items-center gap-6">
                        <a href="#" className="hover:opacity-75">
                            <img src="/static/twitter.svg" alt="Twitter" />
                        </a>
                        <a href="#" className="hover:opacity-75">
                            <img src="/static/discord.svg" alt="Discord" />
                        </a>
                        <a href="#" className="hover:opacity-75">
                            <img src="/static/Vector.svg" alt="Vector" />
                        </a>
                    </div>
                </div>
                <div className="flex gap-8 items-center">
                    <div className="gap-3 flex">
                        <Link to="/" className="[&.active]:font-bold">
                            Dashboard
                        </Link>{' '}
                        <Link to="/subscribe" className="[&.active]:font-bold">
                            Subscribe
                        </Link>
                    </div>
                    <div className="wallet-button-container ">
                        <button onClick={handleConnectWallet} className="" disabled={isLoadingWallet}>
                            {isLoadingWallet ? 'Connecting...' : walletAddress ? truncateAddress(walletAddress) : 'Connect Wallet'}
                        </button>
                        {isDropdownOpen && walletAddress && (
                            <div className="dropdown">
                                <button onClick={handleDisconnect}>Disconnect</button>
                            </div>
                        )}
                    </div>
                </div>
            </nav>
        </header>
    )
}

export default Header;