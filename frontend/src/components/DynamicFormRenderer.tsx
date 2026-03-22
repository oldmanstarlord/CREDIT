import React from 'react';

interface FormField {
  name: string;
  label: string;
  type: 'text' | 'number' | 'select' | 'textarea' | 'checkbox' | 'date';
  required?: boolean;
  options?: { value: string; label: string }[];
  placeholder?: string;
  min?: number;
  max?: number;
}

interface DynamicFormRendererProps {
  category: string;
  formData: Record<string, any>;
  onChange: (name: string, value: any) => void;
  errors?: Record<string, string>;
}

const CATEGORY_FIELDS: Record<string, FormField[]> = {
  farmer: [
    { name: 'land_size', label: 'Land Size (acres)', type: 'number', required: true, min: 0.1 },
    { name: 'land_location_state', label: 'State', type: 'text', required: true },
    { name: 'land_location_district', label: 'District', type: 'text', required: true },
    { name: 'crop_type', label: 'Primary Crop', type: 'select', required: true, options: [
      { value: 'wheat', label: 'Wheat' },
      { value: 'rice', label: 'Rice' },
      { value: 'sugarcane', label: 'Sugarcane' },
      { value: 'cotton', label: 'Cotton' },
      { value: 'vegetables', label: 'Vegetables' },
    ]},
    { name: 'irrigation_type', label: 'Irrigation Type', type: 'select', required: true, options: [
      { value: 'rainfed', label: 'Rainfed' },
      { value: 'canal', label: 'Canal' },
      { value: 'borewell', label: 'Borewell' },
    ]},
    { name: 'annual_income_estimate', label: 'Annual Income (₹)', type: 'number', required: true, min: 10000 },
    { name: 'kisan_credit_card_number', label: 'Kisan Credit Card Number (optional)', type: 'text' },
  ],
  daily_wage_worker: [
    { name: 'occupation_type', label: 'Type of Work', type: 'text', required: true, placeholder: 'e.g., Construction, Loading' },
    { name: 'average_daily_earnings', label: 'Average Daily Earnings (₹)', type: 'number', required: true, min: 100 },
    { name: 'days_worked_per_month', label: 'Days Worked Per Month', type: 'number', required: true, min: 1, max: 30 },
    { name: 'work_consistency', label: 'Work Consistency', type: 'select', required: true, options: [
      { value: 'regular', label: 'Regular (same employer)' },
      { value: 'irregular', label: 'Irregular (different sites)' },
      { value: 'seasonal', label: 'Seasonal' },
    ]},
    { name: 'has_bank_account', label: 'Do you have a bank account?', type: 'checkbox' },
  ],
  gig_worker: [
    { name: 'platforms', label: 'Platforms (comma-separated)', type: 'text', required: true, placeholder: 'e.g., Ola, Zomato, Uber' },
    { name: 'average_weekly_earnings', label: 'Average Weekly Earnings (₹)', type: 'number', required: true, min: 500 },
    { name: 'active_days_per_week', label: 'Active Days Per Week', type: 'number', required: true, min: 1, max: 7 },
    { name: 'months_on_platform', label: 'Months on Platform', type: 'number', required: true, min: 1 },
  ],
  msme_owner: [
    { name: 'business_type', label: 'Business Type', type: 'text', required: true, placeholder: 'e.g., Retail Shop, Manufacturing' },
    { name: 'business_age_months', label: 'Business Age (months)', type: 'number', required: true, min: 1 },
    { name: 'monthly_revenue', label: 'Monthly Revenue (₹)', type: 'number', required: true, min: 1000 },
    { name: 'monthly_expenses', label: 'Monthly Expenses (₹)', type: 'number', required: true, min: 0 },
    { name: 'number_of_employees', label: 'Number of Employees', type: 'number', min: 0 },
    { name: 'gst_registration_number', label: 'GST Number (optional)', type: 'text' },
  ],
  homemaker: [
    { name: 'household_monthly_income', label: 'Household Monthly Income (₹)', type: 'number', required: true, min: 5000 },
    { name: 'spouse_employment_status', label: 'Spouse Employment Status', type: 'text', placeholder: 'e.g., Salaried, Self-employed' },
    { name: 'number_of_dependents', label: 'Number of Dependents', type: 'number', required: true, min: 0 },
    { name: 'household_monthly_expenses', label: 'Household Monthly Expenses (₹)', type: 'number', required: true, min: 0 },
  ],
  low_income_salaried: [
    { name: 'employer_name', label: 'Employer Name', type: 'text', required: true },
    { name: 'employer_type', label: 'Employer Type', type: 'select', required: true, options: [
      { value: 'private', label: 'Private Company' },
      { value: 'govt', label: 'Government' },
      { value: 'ngo', label: 'NGO' },
      { value: 'informal', label: 'Informal Sector' },
    ]},
    { name: 'monthly_salary_net', label: 'Monthly Take-Home Salary (₹)', type: 'number', required: true, min: 5000 },
    { name: 'employment_tenure_months', label: 'Employment Tenure (months)', type: 'number', required: true, min: 1 },
    { name: 'salary_credited_to_bank', label: 'Salary credited to bank account?', type: 'checkbox' },
    { name: 'bank_name', label: 'Bank Name (optional)', type: 'text' },
  ],
};

const DynamicFormRenderer: React.FC<DynamicFormRendererProps> = ({
  category,
  formData,
  onChange,
  errors = {},
}) => {
  const fields = CATEGORY_FIELDS[category] || [];

  const renderField = (field: FormField) => {
    const value = formData[field.name] || '';
    const error = errors[field.name];

    const baseClasses = `w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
      error ? 'border-red-500' : 'border-gray-300'
    }`;

    switch (field.type) {
      case 'select':
        return (
          <select
            value={value}
            onChange={(e) => onChange(field.name, e.target.value)}
            className={baseClasses}
            required={field.required}
          >
            <option value="">Select {field.label}</option>
            {field.options?.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        );

      case 'textarea':
        return (
          <textarea
            value={value}
            onChange={(e) => onChange(field.name, e.target.value)}
            className={baseClasses}
            placeholder={field.placeholder}
            required={field.required}
            rows={3}
          />
        );

      case 'checkbox':
        return (
          <div className="flex items-center">
            <input
              type="checkbox"
              checked={!!value}
              onChange={(e) => onChange(field.name, e.target.checked)}
              className="w-5 h-5 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
            />
            <label className="ml-2 text-sm text-gray-700">{field.label}</label>
          </div>
        );

      case 'number':
        return (
          <input
            type="number"
            value={value}
            onChange={(e) => onChange(field.name, parseFloat(e.target.value) || '')}
            className={baseClasses}
            placeholder={field.placeholder}
            required={field.required}
            min={field.min}
            max={field.max}
            step="any"
          />
        );

      case 'date':
        return (
          <input
            type="date"
            value={value}
            onChange={(e) => onChange(field.name, e.target.value)}
            className={baseClasses}
            required={field.required}
          />
        );

      default:
        return (
          <input
            type="text"
            value={value}
            onChange={(e) => onChange(field.name, e.target.value)}
            className={baseClasses}
            placeholder={field.placeholder}
            required={field.required}
          />
        );
    }
  };

  return (
    <div className="space-y-6">
      {fields.map((field) => (
        <div key={field.name}>
          {field.type !== 'checkbox' && (
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {field.label}
              {field.required && <span className="text-red-500 ml-1">*</span>}
            </label>
          )}
          {renderField(field)}
          {errors[field.name] && (
            <p className="mt-1 text-sm text-red-600">{errors[field.name]}</p>
          )}
        </div>
      ))}
    </div>
  );
};

export default DynamicFormRenderer;
