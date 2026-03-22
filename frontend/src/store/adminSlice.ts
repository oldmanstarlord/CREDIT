import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { adminService, AdminApplication, ApplicationDetail, DashboardKPIs } from '../services/adminService';

interface AdminState {
  applications: AdminApplication[];
  totalApplications: number;
  selectedApplication: ApplicationDetail | null;
  kpis: DashboardKPIs | null;
  fairnessReport: any;
  portfolioRisk: any;
  detailPanelOpen: boolean;
  loading: boolean;
  error: string | null;
  filters: {
    stage: string;
    status_filter: string;
    category: string;
    sort_by: string;
    sort_order: string;
    offset: number;
    limit: number;
  };
}

const initialState: AdminState = {
  applications: [],
  totalApplications: 0,
  selectedApplication: null,
  kpis: null,
  fairnessReport: null,
  portfolioRisk: null,
  detailPanelOpen: false,
  loading: false,
  error: null,
  filters: {
    stage: '',
    status_filter: '',
    category: '',
    sort_by: 'created_at',
    sort_order: 'desc',
    offset: 0,
    limit: 20,
  },
};

export const fetchApplications = createAsyncThunk(
  'admin/fetchApplications',
  async (params: any, { rejectWithValue }) => {
    try {
      const res = await adminService.getApplications(params);
      return res.data;
    } catch (err: any) {
      return rejectWithValue(err.response?.data?.detail || 'Failed to fetch applications');
    }
  }
);

export const fetchApplicationDetail = createAsyncThunk(
  'admin/fetchDetail',
  async (id: string, { rejectWithValue }) => {
    try {
      const res = await adminService.getApplicationDetail(id);
      return res.data;
    } catch (err: any) {
      return rejectWithValue(err.response?.data?.detail || 'Failed to fetch detail');
    }
  }
);

export const fetchKPIs = createAsyncThunk(
  'admin/fetchKPIs',
  async (days: number = 30, { rejectWithValue }) => {
    try {
      const res = await adminService.getKPIs(days);
      return res.data;
    } catch (err: any) {
      return rejectWithValue(err.response?.data?.detail || 'Failed to fetch KPIs');
    }
  }
);

export const fetchFairnessReport = createAsyncThunk(
  'admin/fetchFairness',
  async (days: number = 30, { rejectWithValue }) => {
    try {
      const res = await adminService.getFairnessReport(days);
      return res.data;
    } catch (err: any) {
      return rejectWithValue('Failed to fetch fairness report');
    }
  }
);

export const fetchPortfolioRisk = createAsyncThunk(
  'admin/fetchPortfolio',
  async (_, { rejectWithValue }) => {
    try {
      const res = await adminService.getPortfolioRisk();
      return res.data;
    } catch (err: any) {
      return rejectWithValue('Failed to fetch portfolio risk');
    }
  }
);

const adminSlice = createSlice({
  name: 'admin',
  initialState,
  reducers: {
    openDetailPanel(state) { state.detailPanelOpen = true; },
    closeDetailPanel(state) { state.detailPanelOpen = false; state.selectedApplication = null; },
    setFilters(state, action) { state.filters = { ...state.filters, ...action.payload }; },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchApplications.pending, (state) => { state.loading = true; })
      .addCase(fetchApplications.fulfilled, (state, action) => {
        state.loading = false;
        state.applications = action.payload.applications;
        state.totalApplications = action.payload.total;
      })
      .addCase(fetchApplications.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      .addCase(fetchApplicationDetail.fulfilled, (state, action) => {
        state.selectedApplication = action.payload;
        state.detailPanelOpen = true;
      })
      .addCase(fetchKPIs.fulfilled, (state, action) => { state.kpis = action.payload; })
      .addCase(fetchFairnessReport.fulfilled, (state, action) => { state.fairnessReport = action.payload; })
      .addCase(fetchPortfolioRisk.fulfilled, (state, action) => { state.portfolioRisk = action.payload; });
  },
});

export const { openDetailPanel, closeDetailPanel, setFilters } = adminSlice.actions;
export default adminSlice.reducer;
