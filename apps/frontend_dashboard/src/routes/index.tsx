import { useState, useEffect } from 'react';
import '../Dashboard.css';
import { createFileRoute } from '@tanstack/react-router'
import Header from '../components/Header';
import { useAppContext } from '../AppContext';

export const Route = createFileRoute('/')({
  component: Dashboard,
})

function Dashboard() {
  const { walletAddress } = useAppContext();
  const [balances, setBalances] = useState(null);
  const [network, setNetwork] = useState(null);
  const [error, setError] = useState(null);
  const [history, setHistory] = useState<any[] | null>(null);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const [isLoadingWallet, setIsLoadingWallet] = useState(false);


  useEffect(() => {
    if (walletAddress) {
      loadHistory();
    }
  }, [walletAddress]);

  const loadHistory = async () => {
    // try {
    //   setIsLoadingHistory(true);
    //   const response = await fetch(`/api/history?wallet_id=${walletAddress}`);
    //   if (response.status === 200) {
    //     const history = await response.json();
    //     setHistory(history || null);
    //   }
    // } catch (e) {

    // }
    // setIsLoadingHistory(false);
  };


  return (
    <div className="bg-[#0c0c0c] min-h-screen w-full flex flex-col ">
      <Header />



      <div className='max-w-6xl mx-auto w-full'>
        {/* <h1>Dashboard</h1> */}
        <div className="p-4 w-full mx-auto max-w-6xl">
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


        <iframe src="http://0.0.0.0:8501" title="Dashboard" className='w-full h-[1000px]' ></iframe>
      </div>


    </div>
  );
}

export default Dashboard;
