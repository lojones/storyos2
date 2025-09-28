import { createAsyncThunk, createSlice, PayloadAction } from '@reduxjs/toolkit';
import { authAPI } from '../../api/client';
import { AuthState, AuthUser, LoginCredentials } from '../../types';

const storedToken = localStorage.getItem('auth_token');
const storedRole = localStorage.getItem('auth_role');
const storedUser = localStorage.getItem('auth_user');

const initialState: AuthState = {
  user: storedUser ? JSON.parse(storedUser) : null,
  token: storedToken,
  role: storedRole,
  isLoading: false,
  error: null
};

export const login = createAsyncThunk(
  'auth/login',
  async ({ username, password }: LoginCredentials) => {
    const response = await authAPI.login(username, password);
    return response.data as { access_token: string; token_type: string; user_role: string };
  }
);

export const fetchCurrentUser = createAsyncThunk('auth/fetchCurrentUser', async () => {
  const response = await authAPI.me();
  return response.data as { user_id: string; role: string };
});

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    logout: (state) => {
      state.user = null;
      state.token = null;
      state.role = null;
      localStorage.removeItem('auth_token');
      localStorage.removeItem('auth_role');
      localStorage.removeItem('auth_user');
    }
  },
  extraReducers: (builder) => {
    builder
      .addCase(login.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(login.fulfilled, (state, action) => {
        state.isLoading = false;
        state.token = action.payload.access_token;
        state.role = action.payload.user_role;
        localStorage.setItem('auth_token', action.payload.access_token);
        localStorage.setItem('auth_role', action.payload.user_role);
      })
      .addCase(login.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message ?? 'Login failed';
      })
      .addCase(fetchCurrentUser.fulfilled, (state, action: PayloadAction<{ user_id: string; role: string }>) => {
        const user: AuthUser = {
          userId: action.payload.user_id,
          role: action.payload.role
        };
        state.user = user;
        state.role = action.payload.role;
        localStorage.setItem('auth_user', JSON.stringify(user));
        if (action.payload.role) {
          localStorage.setItem('auth_role', action.payload.role);
        }
      })
      .addCase(fetchCurrentUser.rejected, (state) => {
        state.user = null;
      });
  }
});

export const { logout } = authSlice.actions;
export default authSlice.reducer;
