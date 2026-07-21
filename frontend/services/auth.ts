import apiClient from "./api";
import type {
  AuthResponse,
  LoginRequest,
  RegisterRequest,
  UserProfile,
} from "@/types";

// =============================================================================
// Auth API Service
// =============================================================================

export const authApi = {
  /**
   * Register a new user account
   */
  async register(data: RegisterRequest): Promise<AuthResponse> {
    return apiClient.post<AuthResponse>("/auth/register", data);
  },

  /**
   * Login with email and password
   */
  async login(data: LoginRequest): Promise<AuthResponse> {
    return apiClient.post<AuthResponse>("/auth/login", data);
  },

  /**
   * Refresh the access token using the httpOnly refresh cookie
   */
  async refresh(): Promise<AuthResponse> {
    return apiClient.post<AuthResponse>("/auth/refresh");
  },

  /**
   * Get the currently authenticated user's profile
   */
  async getMe(): Promise<UserProfile> {
    return apiClient.get<UserProfile>("/auth/me");
  },

  /**
   * Logout by clearing the refresh token cookie on the server
   */
  async logout(): Promise<void> {
    await apiClient.post<void>("/auth/logout");
  },
};

export default authApi;
