"use client";

import {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
  type ReactNode,
} from "react";
import { useQueryClient } from "@tanstack/react-query";
import { authApi } from "@/services/auth";
import {
  setAccessToken as setApiToken,
} from "@/services/api";
import type {
  AuthResponse,
  AuthState,
  LoginRequest,
  RegisterRequest,
  UserProfile,
} from "@/types";

// =============================================================================
// Auth Context
// =============================================================================

interface AuthContextValue extends AuthState {
  login: (data: LoginRequest) => Promise<void>;
  register: (data: RegisterRequest) => Promise<void>;
  logout: () => Promise<void>;
  setAccessToken: (token: string | null) => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

// =============================================================================
// Auth Provider
// =============================================================================

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const queryClient = useQueryClient();

  const [state, setState] = useState<AuthState>({
    user: null,
    accessToken: null,
    isLoading: true,
    isAuthenticated: false,
  });

  const setAccessToken = useCallback((token: string | null) => {
    setState((prev) => ({
      ...prev,
      accessToken: token,
      isAuthenticated: !!token && !!prev.user,
    }));
  }, []);

  /**
   * Attempt to restore the session on mount by calling /auth/me.
   * If the refresh cookie is still valid, the backend returns user data
   * and we also get a fresh access token from the /refresh endpoint.
   */
  useEffect(() => {
    let cancelled = false;

    async function restoreSession() {
      try {
        // Try to refresh first — this sets a new access token + rotates
        // the refresh cookie.
        const refreshed: AuthResponse = await authApi.refresh();
        if (!cancelled) {
          setState({
            user: refreshed.user,
            accessToken: refreshed.access_token,
            isLoading: false,
            isAuthenticated: true,
          });
          return;
        }
      } catch {
        // Refresh failed — try just fetching /auth/me
        try {
          const user: UserProfile = await authApi.getMe();
          if (!cancelled) {
            setState({
              user,
              accessToken: null,
              isLoading: false,
              isAuthenticated: true,
            });
            return;
          }
        } catch {
          // No valid session
          if (!cancelled) {
            setState({
              user: null,
              accessToken: null,
              isLoading: false,
              isAuthenticated: false,
            });
          }
        }
      }
    }

    restoreSession();

    return () => {
      cancelled = true;
    };
  }, []);

  const updateTokens = useCallback(
    (accessToken: string | null, user: UserProfile | null) => {
      setApiToken(accessToken);
      setState((prev) => ({
        ...prev,
        user,
        accessToken,
        isAuthenticated: !!accessToken && !!user,
      }));
    },
    []
  );

  const login = useCallback(
    async (data: LoginRequest) => {
      const response: AuthResponse = await authApi.login(data);
      updateTokens(response.access_token, response.user);
      setState((prev) => ({ ...prev, isLoading: false }));
    },
    [updateTokens]
  );

  const register = useCallback(
    async (data: RegisterRequest) => {
      const response: AuthResponse = await authApi.register(data);
      updateTokens(response.access_token, response.user);
      setState((prev) => ({ ...prev, isLoading: false }));
    },
    [updateTokens]
  );

  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    } catch {
      // Best-effort — clear local state even if the request fails
    }

    // Clear all React Query caches
    queryClient.clear();
    updateTokens(null, null);
    setState({
      user: null,
      accessToken: null,
      isLoading: false,
      isAuthenticated: false,
    });
  }, [queryClient, updateTokens]);

  // Listen for auth:expired events from the API interceptor
  useEffect(() => {
    const handler = () => {
      updateTokens(null, null);
      setState({
        user: null,
        accessToken: null,
        isLoading: false,
        isAuthenticated: false,
      });
    };
    window.addEventListener("auth:expired", handler);
    return () => window.removeEventListener("auth:expired", handler);
  }, [updateTokens]);

  // Update api.ts token store whenever accessToken changes
  useEffect(() => {
    setApiToken(state.accessToken);
  }, [state.accessToken]);

  return (
    <AuthContext.Provider
      value={{
        ...state,
        login,
        register,
        logout,
        setAccessToken,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

// =============================================================================
// Hook
// =============================================================================

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}

export default AuthProvider;
