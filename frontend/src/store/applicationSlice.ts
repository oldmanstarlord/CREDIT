import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { applicationService, CreditScoreResponse, ApplicationResponse, SimulateResponse } from '../services/applicationService';

interface ApplicationState {
  currentStep: number;
  formData: Record<string, any>;
  submissionResult: ApplicationResponse | null;
  scoreResult: CreditScoreResponse | null;
  simulationResult: SimulateResponse | null;
  loading: boolean;
  submitting: boolean;
  error: string | null;
}

const initialState: ApplicationState = {
  currentStep: 0,
  formData: {},
  submissionResult: null,
  scoreResult: null,
  simulationResult: null,
  loading: false,
  submitting: false,
  error: null,
};

export const submitApplication = createAsyncThunk(
  'application/submit',
  async (data: any, { rejectWithValue }) => {
    try {
      const res = await applicationService.submit(data);
      return res.data;
    } catch (err: any) {
      return rejectWithValue(err.response?.data?.detail || 'Submission failed');
    }
  }
);

export const fetchScore = createAsyncThunk(
  'application/fetchScore',
  async (applicationId: string, { rejectWithValue }) => {
    try {
      const res = await applicationService.getScore(applicationId);
      return res.data;
    } catch (err: any) {
      return rejectWithValue(err.response?.data?.detail || 'Failed to fetch score');
    }
  }
);

export const runSimulation = createAsyncThunk(
  'application/simulate',
  async ({ id, data }: { id: string; data: any }, { rejectWithValue }) => {
    try {
      const res = await applicationService.simulate(id, data);
      return res.data;
    } catch (err: any) {
      return rejectWithValue(err.response?.data?.detail || 'Simulation failed');
    }
  }
);

const applicationSlice = createSlice({
  name: 'application',
  initialState,
  reducers: {
    setStep(state, action: PayloadAction<number>) {
      state.currentStep = action.payload;
    },
    updateFormData(state, action: PayloadAction<Record<string, any>>) {
      state.formData = { ...state.formData, ...action.payload };
    },
    resetApplication(state) {
      Object.assign(state, initialState);
    },
    clearSimulation(state) {
      state.simulationResult = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(submitApplication.pending, (state) => { state.submitting = true; state.error = null; })
      .addCase(submitApplication.fulfilled, (state, action) => {
        state.submitting = false;
        state.submissionResult = action.payload;
      })
      .addCase(submitApplication.rejected, (state, action) => {
        state.submitting = false;
        state.error = action.payload as string;
      })
      .addCase(fetchScore.pending, (state) => { state.loading = true; })
      .addCase(fetchScore.fulfilled, (state, action) => {
        state.loading = false;
        state.scoreResult = action.payload;
      })
      .addCase(fetchScore.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      .addCase(runSimulation.fulfilled, (state, action) => {
        state.simulationResult = action.payload;
      });
  },
});

export const { setStep, updateFormData, resetApplication, clearSimulation } = applicationSlice.actions;
export default applicationSlice.reducer;
