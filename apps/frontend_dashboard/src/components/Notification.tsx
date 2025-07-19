import React, { useState, useEffect } from 'react';
import { AlertCircle, Verified } from 'lucide-react';
import Header from './Header';
import { useAppContext } from '../AppContext';



const NotificationSubscription = () => {
  const { walletAddress } = useAppContext();

  const [walletId, setWalletId] = useState('');
  const [telegramId, setTelegramId] = useState('');
  const [healthRatioLevel, setHealthRatioLevel] = useState('');
  const [protocolId, setProtocolId] = useState('');
  const [message, setMessage] = useState<string | null>(null);
  const [messageType, setMessageType] = useState<string | null>(null);
  const [activationLink, setActivationLink] = useState(null);

  // Load protocol IDs from backend
  const [protocolIds, setProtocolIds] = useState<string[]>([]);
  useEffect(() => {
    fetch('/api/protocol-ids')
      .then((res) => res.json())
      .then((data) => setProtocolIds(data.protocol_ids || []))
      .catch((err) => {
        console.error('Failed to load protocol IDs', err);
      });
  }, []);

  useEffect(() => {
     setWalletId(walletAddress || '');
  }, [walletAddress])

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setMessage(null);
    setMessageType(null);
    try {

      const response = await fetch('/api/liquidation-watcher', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          wallet_id: walletId,
          health_ratio_level: parseFloat(healthRatioLevel),
          telegram_id: telegramId,
          protocol_id: protocolId,
        }),
      });
      const result = await response.json();
      if (response.ok) {
        setActivationLink(result.activation_link);
        setMessage(result.messages[0] || 'Subscription created successfully');
        setMessageType(result.message_type || 'success');
      } else {
        setMessage(
          Array.isArray(result.messages)
            ? result.messages.join(', ')
            : 'Failed to create subscription'
        );
        setMessageType(result.message_type || 'error');
      }
    } catch (error) {
      console.error('Error submitting subscription:', error);
      setMessage('Network error. Please try again.');
      setMessageType('error');
    }
  };


  useEffect(() => {
    //TODO test with https! Create an endpoint to return  bot name
    const BOT_NAME = 'xxx';

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
      document.getElementById('tg-login')?.removeChild(script);
    }
  }, []);

  async function onTelegramAuth(user: { id: number }) {
    console.log(user);
    try {
      setTelegramId(String(user.id));
    } catch (e) {

    }
  }


  return (
    <div className="bg-[#0c0c0c] min-h-screen w-full flex flex-col">
      <Header></Header>


      {/* Subscription Form */}
      <div className="w-full px-5 max-w-2xl mx-auto ">
        <form onSubmit={handleSubmit} className="w-full flex flex-col gap-8">
          <div className="text-center w-full">
            <h1 className="text-[#f9f9f9] text-xl w-full font-semibold font-instrument-sans">
              Create subscription
            </h1>
            <p className="text-[#e6ebf0] text-sm font-normal font-open-sans leading-normal mt-3">
              Fill in the form to receive updates on Telegram
            </p>
          </div>


          {/* Wallet ID Input */}
          <div className="flex flex-col gap-3 w-full justify-center">
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
              className="px-4 py-6 w-full  bg-[#1c1c1c] rounded-lg text-[#fefefe] text-sm font-normal font-instrument-sans outline-none"
              required
            />
          </div>


          {/* Health Ratio Level Input */}
          <div className="flex flex-col gap-3 w-full justify-center">
            <label
              htmlFor="health_ratio_level"
              className="text-[#9b9b9b] text-base font-medium font-montserrat text-start"
            >
              Health ratio level: <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              id="health_ratio_level"
              value={healthRatioLevel}
              onChange={(e) => setHealthRatioLevel(e.target.value)}
              placeholder="Enter health ratio level"
              className="px-4 py-6 w-full  bg-[#1c1c1c] rounded-lg text-[#fefefe] text-sm font-normal font-instrument-sans outline-none"
              required
            />
          </div>

          {/* Protocol ID Select */}
          <div className="flex flex-col gap-3 w-full justify-center">
            <label
              htmlFor="protocol_id"
              className="text-[#9b9b9b] text-base font-medium font-montserrat text-start"
            >
              Protocol ID: <span className="text-red-500">*</span>
            </label>
            <select
              id="protocol_id"
              value={protocolId}
              onChange={(e) => setProtocolId(e.target.value)}
              className="px-4 py-6 w-full  bg-[#1c1c1c] rounded-lg text-[#fefefe] text-sm font-normal font-instrument-sans outline-none border-r-8 border-[#1c1c1c]"
              required
            >
              <option value="">Select a Protocol</option>
              {protocolIds.map((id) => (
                <option key={id} value={id}>{id}</option>
              ))}
            </select>
          </div>


          {/* Telegram ID Input */}
          <div className="flex flex-col gap-3 w-full  justify-center ">
            <label
              htmlFor="wallet_id"
              className="text-[#9b9b9b] text-base font-medium font-montserrat text-start"
            >
              Telegram id: <span className="text-red-500">*</span>
            </label>
            <div className='w-full p-0 flex gap-3'>
              <input
                type="text"
                id="telegram_id"
                onChange={(e) => setTelegramId(e.target.value)}
                value={telegramId}
                placeholder="Paste your telegram id or Login with Telegram"
                className="px-4 py-6 w-full  bg-[#1c1c1c] grow-1 rounded-lg text-[#fefefe] text-sm font-normal font-instrument-sans outline-none"
                required
              />

              <button
                type="button"
                onClick={() => onTelegramAuth({ id: 123456789 })}
                className=" px-6 py-3 rounded-lg border border-[#ffb80d] justify-center items-center gap-2 inline-flex hover:bg-basefull text-[#ffb80d] hover:text-[#fff] text-sm font-medium font-instrument-sans transition-colors"
              >
                Login
              </button>
            </div>

          </div>

          {/* Submit Button */}
          <div className="submit w-full mt-5">
            <button
              type="submit"
              className="h-[60px] w-full  px-6 py-3 rounded-lg border border-[#ffb80d] justify-center items-center gap-2 inline-flex hover:bg-basefull text-[#ffb80d] hover:text-[#fff] text-sm font-medium font-instrument-sans transition-colors"
            >
              Subscribe
            </button>
          </div>

        </form>

        {/* Notification Modal */}
        {message && (
          <div className="fixed inset-0 bg-[#0c0c0c]/25 backdrop-blur-sm grid place-items-center z-50">
            <div className={`
              w-lg  p-5
              
              bg-[#0c0c0c]
              rounded-lg 
              border 
              ${messageType === 'error' ? 'border-[#720000]' : 'border-[#362000]'}
              flex flex-col justify-center items-center gap-12
            `}>
              <div className={`
                text-[#fefefe] 
                text-md 
                font-bold 
                font-instrument-sans
                ${messageType === 'error' ? 'hidden' : ''}
              `}>
                Subscription created successfully
              </div>


              <div className={`
                flex 
                justify-center 
                items-center 
                gap-2
                ${messageType === 'success' ? 'hidden' : ''}
              `}>
                <div className="text-[#fefefe] text-md font-bold font-instrument-sans">
                  Subscription was NOT created successfully
                </div>
                <AlertCircle className="h-6 w-6 text-red-500" />
              </div>



              <div className="flex-col justify-start items-center gap-6 flex">
                <div className="flex justify-center items-center gap-2 text-center text-[#fefefe] text-sm font-normal font-instrument-sans">
                  {message}
                  {messageType === 'success' && (
                    <Verified className="h-6 w-6 text-green-500" />
                  )}
                </div>
                {messageType !== 'error' && (
                  <div className='text-center text-sm'>
                    Navigate to this <a href={activationLink!} target="_blank" rel="noopener noreferrer">link</a>  to allow the bot to send updates
                  </div>
                )}
                <button
                  onClick={() => setMessage(null)}
                  className="self-stretch mt-5 h-12 px-6 py-3 rounded-lg border border-basefull justify-center items-center gap-2 inline-flex text-basefull text-sm font-medium font-instrument-sans cursor-pointer hover:bg-basefull hover:text-basebg hover:border-basebg"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      <div id="tg-login" className='hidden'></div>
    </div>
  );
};

export default NotificationSubscription;
