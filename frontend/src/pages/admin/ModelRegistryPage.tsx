import React, { useEffect, useState } from 'react';
import { Cpu, AlertCircle } from 'lucide-react';
import ModelRegistry from '../../components/ModelRegistry';
import { adminService } from '../../services/adminService';

interface ModelVersion {
  id: string;
  version: string;
  name: string;
  status: 'active' | 'staging' | 'archived';
  accuracy: number;
  auc: number;
  precision: number;
  recall: number;
  f1_score: number;
  deployed_at?: string;
  trained_at: string;
  training_samples: number;
  features_count: number;
  artifact_path: string;
  notes?: string;
}

const ModelRegistryPage: React.FC = () => {
  const [models, setModels] = useState<ModelVersion[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchModels();
  }, []);

  const fetchModels = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await adminService.getModelRegistry();
      setModels(data.models);
    } catch (err: any) {
      console.error('Error fetching models:', err);
      setError(err.message || 'Failed to load model registry');
    } finally {
      setLoading(false);
    }
  };

  const handleDeploy = async (modelId: string) => {
    try {
      await adminService.deployModel(modelId);
      await fetchModels(); // Refresh list
    } catch (err: any) {
      throw new Error(err.message || 'Failed to deploy model');
    }
  };

  const handleArchive = async (modelId: string) => {
    try {
      await adminService.archiveModel(modelId);
      await fetchModels(); // Refresh list
    } catch (err: any) {
      alert(err.message || 'Failed to archive model');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Cpu size={22} className="text-admin-accent" />
          <h1 className="text-2xl font-display font-bold text-admin-text">Model Registry</h1>
        </div>
        <span className="text-xs text-admin-muted font-body">
          {models.length} model{models.length !== 1 ? 's' : ''} registered
        </span>
      </div>

      {loading && (
        <div className="bg-admin-surface border border-admin-border rounded-card p-6 text-center">
          <p className="text-admin-muted">Loading model registry...</p>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-card p-4">
          <div className="flex items-start gap-3">
            <AlertCircle size={18} className="text-red-600 mt-0.5" />
            <div>
              <h3 className="text-sm font-semibold text-red-800 mb-1">Error Loading Models</h3>
              <p className="text-sm text-red-700">{error}</p>
            </div>
          </div>
        </div>
      )}

      {!loading && !error && models.length > 0 && (
        <ModelRegistry
          models={models}
          onDeploy={handleDeploy}
          onArchive={handleArchive}
        />
      )}

      {!loading && !error && models.length === 0 && (
        <div className="bg-admin-surface border border-admin-border rounded-card p-6 text-center">
          <p className="text-admin-muted">No models found in registry</p>
        </div>
      )}
    </div>
  );
};

export default ModelRegistryPage;
