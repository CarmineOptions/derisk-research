import React, { useState } from 'react';
import { AlertCircle, Verified } from 'lucide-react';

const NotificationSubscription = () => {
  const [walletId, setWalletId] = useState('');
  const [healthRatioLevel, setHealthRatioLevel] = useState('');
  const [protocolId, setProtocolId] = useState('');
  const [message, setMessage] = useState<string | null>(null);
  const [messageType, setMessageType] = useState<string | null>(null);

  // Dummy protocol IDs (would typically come from props or context)
  const protocolIds = ['Protocol 1', 'Protocol 2', 'Protocol 3'];

  const handleSubmit = (e : React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    // Placeholder for submission logic
    console.log('Submitting:', { walletId, healthRatioLevel, protocolId });
    // For demonstration, simulate a success/error response
    if (walletId && healthRatioLevel && protocolId) {
      setMessage('Subscription created successfully');
      setMessageType('success');
    } else {
      setMessage('Subscription was NOT created successfully');
      setMessageType('error');
    }
  };

  return (
    <div className="bg-basebg min-h-screen flex flex-col">
      {/* Header */}
      <header className="grid place-items-center mt-8 mb-12">
        <nav className="flex items-center justify-between h-[5.5rem] w-full lg:w-[70rem] rounded-2xl shadow-carmine px-6 py-5">
          <div className="flex justify-center items-center gap-8">
            <div>
              <a href="/" className="no-underline">
                <img 
                  src="/Carmine_logo.svg" 
                  alt="Carmine Logo" 
                />
              </a>
            </div>
            <div className="hidden lg:flex space-between justify-center items-center gap-6">
              <a href="#" className="hover:opacity-75">
                <img src="/twitter.svg" alt="Twitter" />
              </a>
              <a href="#" className="hover:opacity-75">
                <img src="/discord.svg" alt="Discord" />
              </a>
              <a href="#" className="hover:opacity-75">
                <img src="/Vector.svg" alt="Vector" />
              </a>
            </div>
          </div>
          <div>
            <button
              className="group border border-basefull rounded-lg flex gap-2 px-6 py-3 text-basefull text-sm font-instrument-sans font-medium hover:border-0 hover:bg-basefull hover:text-basebg transition-colors"
            >
              <span>Connect Wallet</span>
              <span className="hidden lg:block">
                <img
                  src="/arrow.svg"
                  alt="Arrow"
                  className="block group-hover:hidden"
                />
                <img
                  src="/barrow.svg"
                  alt="Hover Arrow"
                  className="hidden group-hover:block"
                />
              </span>
            </button>
          </div>
        </nav>
      </header>

      {/* Subscription Form */}
      <div className="w-full px-5">
        <form onSubmit={handleSubmit} className="w-full">
          <h1 className="text-[#f9f9f9] text-xl font-semibold font-instrument-sans text-center mb-12">
            Create subscription
          </h1>
          <p className="text-[#e6ebf0] text-sm italic text-center font-normal font-open-sans leading-normal mb-6">
            Fill in these details to create a new subscription
          </p>
          
          <div className="flex flex-col gap-12 w-full justify-center items-center">
            {/* Wallet ID Input */}
            <div className="flex flex-col gap-3 w-full lg:w-auto justify-center">
              <label 
                htmlFor="wallet_id" 
                className="text-[#9b9b9b] text-base font-medium font-montserrat text-start"
              >
                Wallet ID: <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                id="wallet_id"
                value={walletId}
                onChange={(e) => setWalletId(e.target.value)}
                placeholder="Enter your wallet address"
                className="px-4 py-6 w-full lg:w-[44rem] bg-[#1c1c1c] rounded-lg text-[#fefefe] text-sm font-normal font-instrument-sans outline-none"
                required
              />
            </div>

            {/* Health Ratio Level Input */}
            <div className="flex flex-col gap-3 w-full lg:w-auto justify-center">
              <label 
                htmlFor="health_ratio_level" 
                className="text-[#9b9b9b] text-base font-medium font-montserrat"
              >
                Health ratio level: <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                id="health_ratio_level"
                value={healthRatioLevel}
                onChange={(e) => setHealthRatioLevel(e.target.value)}
                placeholder="Enter health ratio level"
                className="px-4 py-6 w-full lg:w-[44rem] bg-[#1c1c1c] rounded-lg text-[#fefefe] text-sm font-normal font-instrument-sans outline-none"
                required
              />
            </div>

            {/* Protocol ID Select */}
            <div className="flex flex-col gap-3 w-full lg:w-auto justify-center">
              <label 
                htmlFor="protocol_id" 
                className="text-[#9b9b9b] text-base font-medium font-montserrat"
              >
                Protocol ID: <span className="text-red-500">*</span>
              </label>
              <select
                id="protocol_id"
                value={protocolId}
                onChange={(e) => setProtocolId(e.target.value)}
                className="px-4 py-6 w-full lg:w-[44rem] bg-[#1c1c1c] rounded-lg text-[#fefefe] text-sm font-normal font-instrument-sans outline-none border-r-8 border-[#1c1c1c]"
                required
              >
                <option value="">Select a Protocol</option>
                {protocolIds.map((id) => (
                  <option key={id} value={id}>{id}</option>
                ))}
              </select>
            </div>

            {/* Submit Button */}
            <div className="submit w-full lg:w-auto">
              <button
                type="submit"
                className="h-[60px] w-full lg:w-[44rem] px-6 py-3 rounded-lg border border-[#ffb80d] justify-center items-center gap-2 inline-flex hover:bg-basefull text-[#ffb80d] hover:text-[#0c0c0c] text-sm font-medium font-instrument-sans transition-colors"
              >
                Subscribe
              </button>
            </div>
          </div>
        </form>

        {/* Notification Modal */}
        {message && (
          <div className="fixed inset-0 bg-basebg/25 backdrop-blur-sm grid place-items-center z-50">
            <div className={`
              w-[22rem] lg:w-[43.5rem] 
              h-[28rem] lg:h-[26.25rem] 
              lg:px-20 py-[3.75rem] 
              bg-basebg 
              rounded-lg 
              border 
              ${messageType === 'error' ? 'border-[#720000]' : 'border-[#362000]'}
              flex flex-col justify-center items-center gap-12
            `}>
              <h1 className={`
                text-[#fefefe] 
                text-sm 
                font-bold 
                font-instrument-sans
                ${messageType === 'error' ? 'hidden' : ''}
              `}>
                Subscription created successfully
              </h1>

              <div className={`
                flex 
                justify-center 
                items-center 
                gap-2
                ${messageType === 'success' ? 'hidden' : ''}
              `}>
                <h1 className="text-[#fefefe] text-sm font-bold font-instrument-sans">
                  Subscription was NOT created successfully
                </h1>
                <AlertCircle className="h-6 w-6 text-red-500" />
              </div>

              <div className="h-[89px] flex-col justify-start items-center gap-6 flex">
                <div className="flex justify-center items-center gap-2 text-center text-[#fefefe] text-sm font-normal font-instrument-sans">
                  {message}
                  {messageType === 'success' && (
                    <Verified className="h-6 w-6 text-green-500" />
                  )}
                </div>

                <button 
                  onClick={() => setMessage(null)}
                  className="self-stretch h-12 px-6 py-3 rounded-lg border border-basefull justify-center items-center gap-2 inline-flex text-basefull text-sm font-medium font-instrument-sans cursor-pointer hover:bg-basefull hover:text-basebg hover:border-basebg"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default NotificationSubscription;