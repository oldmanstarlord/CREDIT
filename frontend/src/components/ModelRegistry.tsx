import React, { useState } from 'react';
import { Package, CheckCircle, Clock, XCircle, TrendingUp, Download, Upload, AlertTriangle } from 'lucide-react';

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

interface ModelRegistryProps {
  models: ModelVersion[];
  onDeploy: (modelId: string) => Promise<void>;
  onArchive: (modelId: string) => Promise<void>;
}

const ModelRegistry: React.FC<ModelRegistryProps> = ({ models, onDeploy, onArchive }) => {
  const [selectedModel, setSelectedModel] = useState<ModelVersion | null>(null);
  const [isDeploying, setIsDeploying] = useState(false);

  const getStatusConfig = (status: string) => {
    if (status === 'active') {
      return { label: 'ACTIVE', color: 'text-risk-low', bgColor: 'bg-green-100', icon: CheckCircle };
    }
    if (status === 'staging') {
      return { label: 'STAGING', color: 'text-risk-medium', bgColor: 'bg-yellow-100', icon: Clock };
    }
    return { label: 'ARCHIVED', color: 'text-user-muted', bgColor: 'bg-gray-100', icon: XCircle };
  };

  const handleDeploy = async (modelId: string) => {
    if (!confirm('Are you sure you want to deploy this model to production?')) return;
    setIsDeploying(true);
    try {
      await onDeploy(modelId);
      alert('Model deployed successfully');
    } catch (error) {
      alert('Failed to deploy model');
    } finally {
      setIsDeploying(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Active Model Banner */}
      {models.find((m) => m.status === 'active') && (
        <div className="bg-green-50 border border-green-200 rounded-card p-4">
          <div className="flex items-start gap-3">
            <CheckCircle size={20} className="text-risk-low shrink-0 mt-0.5" />
            <div className="flex-1">
              <h3 className="text-sm font-semibold text-risk-low mb-1">
                Currently Active Model
              </h3>
              <p className="text-sm text-user-text">
                {models.find((m) => m.status === 'active')?.name} (v{models.find((m) => m.status === 'active')?.version})
              </p>
              <p className="text-xs text-user-muted mt-1">
                Deployed: {models.find((m) => m.status === 'active')?.deployed_at ? new Date(models.find((m) => m.status === 'active')!.deployed_at!).toLocaleString() : 'N/A'}
              </p>
            </div>
            <div className="text-right">
              <p className="text-xs text-user-muted">AUC Score</p>
              <p className="text-2xl font-bold text-risk-low font-data">
                {models.find((m) => m.status === 'active')?.auc.toFixed(3)}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Model List */}
      <div className="grid grid-cols-1 gap-4">
        {models.map((model) => {
          const statusConfig = getStatusConfig(model.status);
          const Icon = statusConfig.icon;
          return (
            <div
              key={model.id}
              className="bg-white border border-user-border rounded-card p-4 hover:shadow-card-user transition-shadow"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-start gap-3">
                  <div className={`p-2 rounded-lg ${statusConfig.bgColor}`}>
                    <Package size={20} className={statusConfig.color} />
                  </div>
                  <div>
                    <h3 className="text-base font-semibold text-user-text font-heading">
                      {model.name}
                    </h3>
                    <p className="text-sm text-user-muted">
                      Version {model.version} • Trained {new Date(model.trained_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>
                <span className={`px-3 py-1 rounded-pill text-xs font-medium ${statusConfig.bgColor} ${statusConfig.color} flex items-center gap-1`}>
                  <Icon size={14} />
                  {statusConfig.label}
                </span>
              </div>

              {/* Metrics Grid */}
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-4">
                <div>
                  <p className="text-xs text-user-muted mb-1">Accuracy</p>
                  <p className="text-lg font-bold text-user-text font-data">
                    {(model.accuracy * 100).toFixed(1)}%
                  </p>
                </div>
                <div>
                  <p className="text-xs text-user-muted mb-1">AUC</p>
                  <p className="text-lg font-bold text-user-text font-data">
                    {model.auc.toFixed(3)}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-user-muted mb-1">Precision</p>
                  <p className="text-lg font-bold text-user-text font-data">
                    {(model.precision * 100).toFixed(1)}%
                  </p>
                </div>
                <div>
                  <p className="text-xs text-user-muted mb-1">Recall</p>
                  <p className="text-lg font-bold text-user-text font-data">
                    {(model.recall * 100).toFixed(1)}%
                  </p>
                </div>
                <div>
                  <p className="text-xs text-user-muted mb-1">F1 Score</p>
                  <p className="text-lg font-bold text-user-text font-data">
                    {model.f1_score.toFixed(3)}
                  </p>
                </div>
              </div>

              {/* Training Info */}
              <div className="flex items-center gap-4 text-xs text-user-muted mb-4">
                <span>{model.training_samples.toLocaleString()} training samples</span>
                <span>•</span>
                <span>{model.features_count} features</span>
                <span>•</span>
                <span className="font-data">{model.artifact_path.split('/').pop()}</span>
              </div>

              {/* Notes */}
              {model.notes && (
                <div className="bg-blue-50 border border-blue-200 rounded-card p-3 mb-4">
                  <p className="text-xs text-user-text">{model.notes}</p>
                </div>
              )}

              {/* Actions */}
              <div className="flex gap-2">
                {model.status === 'staging' && (
                  <button
                    onClick={() => handleDeploy(model.id)}
                    disabled={isDeploying}
                    className="px-4 py-2 bg-risk-low text-white rounded-card text-sm font-medium hover:bg-green-600 transition-colors disabled:opacity-50 flex items-center gap-2"
                  >
                    <Upload size={14} />
                    Deploy to Production
                  </button>
                )}
                {model.status === 'active' && (
                  <button
                    disabled
                    className="px-4 py-2 bg-gray-100 text-user-muted rounded-card text-sm font-medium cursor-not-allowed"
                  >
                    Currently Active
                  </button>
                )}
                {model.status !== 'archived' && (
                  <button
                    onClick={() => onArchive(model.id)}
                    className="px-4 py-2 border border-user-border text-user-text rounded-card text-sm font-medium hover:bg-gray-50 transition-colors"
                  >
                    Archive
                  </button>
                )}
                <button
                  onClick={() => setSelectedModel(model)}
                  className="px-4 py-2 border border-user-border text-user-text rounded-card text-sm font-medium hover:bg-gray-50 transition-colors flex items-center gap-2"
                >
                  <TrendingUp size={14} />
                  View Details
                </button>
                <button className="px-4 py-2 border border-user-border text-user-text rounded-card text-sm font-medium hover:bg-gray-50 transition-colors flex items-center gap-2">
                  <Download size={14} />
                  Download
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {/* Model Comparison Warning */}
      <div className="bg-yellow-50 border border-yellow-200 rounded-card p-4">
        <div className="flex gap-3">
          <AlertTriangle size={20} className="text-yellow-600 shrink-0 mt-0.5" />
          <div className="text-sm text-yellow-800">
            <p className="font-semibold mb-1">Model Deployment Guidelines</p>
            <ul className="list-disc list-inside space-y-1 text-xs">
              <li>Always test models in staging before production deployment</li>
              <li>Ensure AUC &gt; 0.75 and recall &gt; 0.70 for production models</li>
              <li>Monitor fairness metrics after deployment</li>
              <li>Keep at least one archived version for rollback</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ModelRegistry;
