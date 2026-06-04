import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { authAPI } from '../../services/api';

export const loginUser = createAsyncThunk('auth/login', async (data, { rejectWithValue }) => {
  try {
    const res = await authAPI.login(data);
    localStorage.setItem('access_token', res.data.access_token);
    localStorage.setItem('refresh_token', res.data.refresh_token);
    const me = await authAPI.me();
    return me.data;
  } catch (e) {
    return rejectWithValue(e.response?.data?.detail || 'Login failed');
  }
});

export const signupUser = createAsyncThunk('auth/signup', async (data, { rejectWithValue }) => {
  try {
    const res = await authAPI.signup(data);
    localStorage.setItem('access_token', res.data.access_token);
    localStorage.setItem('refresh_token', res.data.refresh_token);
    const me = await authAPI.me();
    return me.data;
  } catch (e) {
    return rejectWithValue(e.response?.data?.detail || 'Signup failed');
  }
});

export const fetchMe = createAsyncThunk('auth/me', async (_, { rejectWithValue }) => {
  try {
    const res = await authAPI.me();
    return res.data;
  } catch (e) {
    return rejectWithValue('Not authenticated');
  }
});

const authSlice = createSlice({
  name: 'auth',
  initialState: { user: null, loading: false, error: null, initialized: false },
  reducers: {
    logout(state) {
      state.user = null;
      localStorage.clear();
    },
    clearError(state) { state.error = null; },
  },
  extraReducers: (builder) => {
    const handlePending = (state) => { state.loading = true; state.error = null; };
    const handleFulfilled = (state, action) => { state.loading = false; state.user = action.payload; state.initialized = true; };
    const handleRejected = (state, action) => { state.loading = false; state.error = action.payload; state.initialized = true; };
    builder
      .addCase(loginUser.pending, handlePending).addCase(loginUser.fulfilled, handleFulfilled).addCase(loginUser.rejected, handleRejected)
      .addCase(signupUser.pending, handlePending).addCase(signupUser.fulfilled, handleFulfilled).addCase(signupUser.rejected, handleRejected)
      .addCase(fetchMe.pending, (s) => { s.loading = true; })
      .addCase(fetchMe.fulfilled, handleFulfilled)
      .addCase(fetchMe.rejected, (state) => { state.loading = false; state.initialized = true; });
  },
});

export const { logout, clearError } = authSlice.actions;
export default authSlice.reducer;
