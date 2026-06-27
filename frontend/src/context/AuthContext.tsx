import React, { useContext, useState } from "react";
import type { AuthContextInterface, UserProfile } from "../types/auth";


interface Props {
    children: React.ReactNode;
}

export const AuthContext = React.createContext<AuthContextInterface | null>(null);

export const AuthProvider = ({children}: Props) => {


    const [token, setToken] = useState<string | null>(null);
    const [userProfile, setUserProfile] = useState<any | null>(null);
    const [ isLoading] = useState<boolean>(false);


    const login = (newToken: string, userProfile: UserProfile) => {
        setToken(newToken);
        setUserProfile(userProfile);
    };


    const logout = () => {
        setToken(null);
        setUserProfile(null);
    };

    const value: AuthContextInterface = {
        isLoading,
        token,
        userProfile,
        login,
        logout
    }

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}


export const useAuth = () => {
    const authContext = useContext(AuthContext);

    if (authContext === null){
        throw new Error("useAuth must be within an AuthProvider")
    }

    return authContext;
}