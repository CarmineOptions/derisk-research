import { createContext, ReactNode, useContext, useState } from "react";

type IAppContext = {
    walletAddress?: string;
    setWalletAddress: (address: string|undefined) => void;
}

const AppContext = createContext<IAppContext | undefined>(undefined);

export const AppContextProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
    const [walletAddress, setWalletAddress] = useState<string | undefined>(undefined);

    return (
        <AppContext.Provider value={{ walletAddress, setWalletAddress }}>
            {children}
        </AppContext.Provider>
    );
};


export const useAppContext = (): IAppContext => {
    return useContext(AppContext)!;
};