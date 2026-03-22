import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { AppDispatch, RootState } from '../../store/store';
import { setStep, updateFormData, submitApplication } from '../../store/applicationSlice';
import StepIndicator from '../../components/StepIndicator';
import CategorySelector from '../../components/CategorySelector';
import { ArrowLeft, ArrowRight, Upload, CheckCircle, AlertCircle, Loader2, Shield, Sparkles } from 'lucide-react';

const STEPS = ['Personal', 'Category', 'Details', 'Documents', 'Nominee', 'Review'];

const FloatingInput: React.FC<{
  label: string; type?: string; value: string; onChange: (v: string) => void;
  required?: boolean; prefix?: string; pattern?: string; minLength?: number;
}> = ({ label, type = 'text', value, onChange, required, prefix, pattern, minLength }) => (
  <div className="relative">
    {prefix && <span className="absolute left-4 top-4 text-sm text-user-muted font-body">{prefix}</span>}
    <input
      type={type} placeholder=" " value={value}
      onChange={(e) => onChange(e.target.value)}
      className={`peer w-full ${prefix ? 'pl-12' : 'px-4'} pr-4 pt-5 pb-2 border border-user-border rounded-input text-sm font-body focus:outline-none focus:border-barclays-navy transition-colors`}
      required={required} pattern={pattern} minLength={minLength}
    />
    <label className={`absolute ${prefix ? 'left-12' : 'left-4'} top-2 text-xs text-user-muted font-body peer-placeholder-shown:top-4 peer-placeholder-shown:text-sm peer-focus:top-2 peer-focus:text-xs peer-focus:text-barclays-navy transition-all duration-200 ease-spring`}>
      {label}
    </label>
    {value && value.length > 0 && (
      <CheckCircle size={16} className="absolute right-3 top-4 text-barclays-teal animate-fade-in" />
    )}
  </div>
);

const ApplicationPage: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const navigate = useNavigate();
  const { currentStep, formData, submitting } = useSelector((s: RootState) => s.application);
  const [uploadedDocs, setUploadedDocs] = useState<Record<string, File>>({});
  const [landValuation, setLandValuation] = useState<any>(null);
  const [valuating, setValuating] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const update = (data: Record<string, any>) => dispatch(updateFormData(data));
  const next = () => dispatch(setStep(Math.min(currentStep + 1, STEPS.length - 1)));
  const prev = () => dispatch(setStep(Math.max(currentStep - 1, 0)));

  const handleSubmit = async () => {
    setSubmitError(null);
    try {
      const result = await dispatch(submitApplication({
        full_name: formData.full_name,
        date_of_birth: formData.date_of_birth,
        gender: formData.gender,
        phone_number: formData.phone_number,
        email: formData.email,
        aadhaar_number: formData.aadhaar_number,
        user_category: formData.user_category,
        category_data: formData.category_data || {},
        nominee: formData.nominee_name ? {
          full_name: formData.nominee_name,
          relationship: formData.nominee_relationship || 'spouse',
          phone_number: formData.nominee_phone || '+919876543211',
          collateral_type: formData.collateral_type,
          collateral_value: parseInt(formData.collateral_value || '0'),
          monthly_income: parseInt(formData.nominee_income || '0'),
        } : undefined,
        requested_amount: parseInt(formData.loan_amount || '0'),
        requested_tenure_months: parseInt(formData.loan_tenure || '0'),
        loan_purpose: formData.loan_purpose,
      })).unwrap();
      navigate(`/result/${result.application_id}`);
    } catch (err: any) {
      setSubmitError(typeof err === 'string' ? err : 'Submission failed. Please check your details and try again.');
    }
  };

  const estimateLandValue = () => {
    setValuating(true);
    setTimeout(() => {
      setLandValuation({
        estimatedValue: '₹3.2L – ₹4.1L',
        productivity: 7,
        collateral: 'Medium',
        riskNote: 'Seasonal rain dependency',
      });
      setValuating(false);
    }, 2000);
  };

  const renderStep = () => {
    switch (currentStep) {
      case 0: // Personal Details
        return (
          <div className="space-y-4 max-w-lg mx-auto animate-fade-in">
            <h2 className="text-2xl font-display font-bold text-user-text mb-6">Personal Details</h2>
            <FloatingInput label="Full Name" value={formData.full_name || ''} onChange={(v) => update({ full_name: v })} required />
            <FloatingInput label="Date of Birth" type="date" value={formData.date_of_birth || ''} onChange={(v) => update({ date_of_birth: v })} required />
            <FloatingInput label="Phone Number" prefix="+91" value={formData.phone_number || ''} onChange={(v) => update({ phone_number: v })} required />
            <FloatingInput label="Email Address" type="email" value={formData.email || ''} onChange={(v) => update({ email: v })} required />
            <FloatingInput label="Aadhaar Number" value={formData.aadhaar_number || ''} onChange={(v) => update({ aadhaar_number: v })} pattern="^\d{12}$" />
            <div>
              <p className="text-xs text-user-muted mb-2 font-body">Gender (optional — not used in scoring)</p>
              <div className="flex gap-2">
                {['Male', 'Female', 'Prefer not to say'].map((g) => (
                  <button key={g} onClick={() => update({ gender: g.toLowerCase() })}
                    className={`px-4 py-2 text-sm rounded-pill border transition-all ${formData.gender === g.toLowerCase() ? 'bg-barclays-navy text-white border-barclays-navy' : 'border-user-border text-user-muted hover:border-barclays-navy'}`}>
                    {g}
                  </button>
                ))}
              </div>
            </div>
          </div>
        );

      case 1: // Category Selection
        return (
          <div className="animate-fade-in">
            <h2 className="text-2xl font-display font-bold text-user-text mb-2 text-center">What best describes you?</h2>
            <p className="text-sm text-user-muted text-center mb-8 font-body">This helps us tailor the application to your needs.</p>
            <CategorySelector selected={formData.user_category || ''} onSelect={(c) => update({ user_category: c })} />
          </div>
        );

      case 2: // Category-Specific Details
        return (
          <div className="space-y-4 max-w-lg mx-auto animate-fade-in">
            <h2 className="text-2xl font-display font-bold text-user-text mb-6">
              {formData.user_category === 'farmer' ? 'Farm & Land Details' :
               formData.user_category === 'gig_worker' ? 'Platform & Earnings' :
               formData.user_category === 'msme_owner' ? 'Business Details' :
               formData.user_category === 'low_income_salaried' ? 'Employment Details' :
               formData.user_category === 'homemaker' ? 'Household Details' :
               'Work Details'}
            </h2>
            {formData.user_category === 'farmer' && (
              <>
                <FloatingInput label="Land Size (acres)" type="number" value={formData.land_size || ''} onChange={(v) => update({ land_size: v, category_data: { ...formData.category_data, land_size: parseFloat(v) } })} />
                <FloatingInput label="State" value={formData.state || ''} onChange={(v) => update({ state: v, category_data: { ...formData.category_data, land_location_state: v } })} />
                <FloatingInput label="District" value={formData.district || ''} onChange={(v) => update({ district: v, category_data: { ...formData.category_data, land_location_district: v } })} />
                <FloatingInput label="Crop Type" value={formData.crop_type || ''} onChange={(v) => update({ crop_type: v, category_data: { ...formData.category_data, crop_type: v } })} />
                <div>
                  <p className="text-xs text-user-muted mb-2 font-body">Irrigation Type</p>
                  <div className="flex gap-2">
                    {['Rainfed', 'Canal', 'Borewell', 'Drip'].map((t) => (
                      <button key={t} onClick={() => update({ irrigation: t.toLowerCase(), category_data: { ...formData.category_data, irrigation_type: t.toLowerCase() } })}
                        className={`px-3 py-2 text-sm rounded-input border transition-all ${formData.irrigation === t.toLowerCase() ? 'bg-barclays-teal text-white border-barclays-teal' : 'border-user-border text-user-muted'}`}>
                        {t}
                      </button>
                    ))}
                  </div>
                </div>
                <FloatingInput label="Annual Income (₹)" type="number" value={formData.annual_income || ''} onChange={(v) => update({ annual_income: v, category_data: { ...formData.category_data, annual_income_estimate: parseInt(v), monthly_income: parseInt(v) / 12 } })} />
                {/* GenAI Land Valuation */}
                <div className="p-4 rounded-card border border-barclays-lightblue bg-barclays-lightblue/30 mt-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Sparkles size={18} className="text-barclays-teal" />
                    <span className="font-semibold text-sm text-barclays-navy font-body">AI Land Valuation</span>
                  </div>
                  <p className="text-xs text-user-muted mb-3 font-body">We'll estimate your land's current value to strengthen your application.</p>
                  {!landValuation ? (
                    <button onClick={estimateLandValue} disabled={valuating}
                      className="px-4 py-2 bg-barclays-teal text-white text-sm font-medium rounded-input hover:bg-barclays-navy transition-colors flex items-center gap-2 disabled:opacity-60">
                      {valuating ? <><Loader2 size={14} className="animate-spin" /> Analysing...</> : 'Estimate My Land Value'}
                    </button>
                  ) : (
                    <div className="grid grid-cols-2 gap-3 text-sm font-body">
                      <div><span className="text-user-muted">Value:</span> <span className="font-semibold text-barclays-navy">{landValuation.estimatedValue}</span></div>
                      <div><span className="text-user-muted">Productivity:</span> <span className="font-semibold">{landValuation.productivity}/10</span></div>
                      <div><span className="text-user-muted">Collateral:</span> <span className="font-semibold text-barclays-teal">{landValuation.collateral} ✓</span></div>
                      <div><span className="text-user-muted">Risk:</span> <span className="text-risk-medium text-xs">{landValuation.riskNote}</span></div>
                    </div>
                  )}
                </div>
              </>
            )}
            {formData.user_category === 'gig_worker' && (
              <>
                <div>
                  <p className="text-xs text-user-muted mb-2 font-body">Select your platforms</p>
                  <div className="grid grid-cols-4 gap-2">
                    {['Ola', 'Uber', 'Zomato', 'Swiggy', 'Urban Company', 'Rapido', 'Dunzo', 'Other'].map((p) => {
                      const selected = (formData.platforms || []).includes(p);
                      return (
                        <button key={p} onClick={() => {
                          const platforms = selected ? (formData.platforms || []).filter((x: string) => x !== p) : [...(formData.platforms || []), p];
                          update({ platforms, category_data: { ...formData.category_data, platforms, platform_count: platforms.length } });
                        }}
                          className={`p-3 text-xs rounded-input border text-center transition-all ${selected ? 'bg-barclays-teal text-white border-barclays-teal ring-2 ring-barclays-teal/30' : 'border-user-border text-user-muted hover:border-barclays-teal'}`}>
                          {p}
                        </button>
                      );
                    })}
                  </div>
                </div>
                <FloatingInput label="Weekly Earnings (₹)" type="number" value={formData.weekly_earnings || ''} onChange={(v) => update({ weekly_earnings: v, category_data: { ...formData.category_data, average_weekly_earnings: parseInt(v), monthly_income: parseInt(v) * 4.33 } })} />
                <FloatingInput label="Months on Platform" type="number" value={formData.months_on_platform || ''} onChange={(v) => update({ months_on_platform: v, category_data: { ...formData.category_data, months_on_platform: parseInt(v) } })} />
                <FloatingInput label="Active Days per Week" type="number" value={formData.active_days || ''} onChange={(v) => update({ active_days: v, category_data: { ...formData.category_data, active_days_per_week: parseFloat(v) } })} />
              </>
            )}
            {formData.user_category === 'msme_owner' && (
              <>
                <FloatingInput label="Business Type" value={formData.business_type || ''} onChange={(v) => update({ business_type: v, category_data: { ...formData.category_data, business_type: v } })} />
                <FloatingInput label="Business Age (months)" type="number" value={formData.business_age || ''} onChange={(v) => update({ business_age: v, category_data: { ...formData.category_data, business_age_months: parseInt(v) } })} />
                <FloatingInput label="Monthly Revenue (₹)" type="number" value={formData.monthly_revenue || ''} onChange={(v) => update({ monthly_revenue: v, category_data: { ...formData.category_data, monthly_revenue: parseInt(v), monthly_income: parseInt(v) } })} />
                <FloatingInput label="Monthly Expenses (₹)" type="number" value={formData.monthly_expenses || ''} onChange={(v) => update({ monthly_expenses: v, category_data: { ...formData.category_data, monthly_expenses: parseInt(v) } })} />
                <FloatingInput label="GST Number (optional)" value={formData.gst || ''} onChange={(v) => update({ gst: v, category_data: { ...formData.category_data, gst_registration_number: v } })} />
              </>
            )}
            {formData.user_category === 'low_income_salaried' && (
              <>
                <FloatingInput label="Employer Name" value={formData.employer || ''} onChange={(v) => update({ employer: v, category_data: { ...formData.category_data, employer_name: v } })} />
                <div>
                  <p className="text-xs text-user-muted mb-2 font-body">Employer Type</p>
                  <div className="flex gap-2">
                    {['Private', 'Government', 'NGO', 'Informal'].map((t) => (
                      <button key={t} onClick={() => update({ employer_type: t.toLowerCase(), category_data: { ...formData.category_data, employer_type: t.toLowerCase() } })}
                        className={`px-3 py-2 text-sm rounded-input border transition-all ${formData.employer_type === t.toLowerCase() ? 'bg-barclays-navy text-white border-barclays-navy' : 'border-user-border text-user-muted'}`}>
                        {t}
                      </button>
                    ))}
                  </div>
                </div>
                <FloatingInput label="Monthly Salary (₹)" type="number" value={formData.monthly_salary || ''} onChange={(v) => update({ monthly_salary: v, category_data: { ...formData.category_data, monthly_salary_net: parseInt(v), monthly_income: parseInt(v) } })} />
                <FloatingInput label="Employment Tenure (months)" type="number" value={formData.employment_tenure || ''} onChange={(v) => update({ employment_tenure: v, category_data: { ...formData.category_data, employment_tenure_months: parseInt(v) } })} />
              </>
            )}
            {formData.user_category === 'homemaker' && (
              <>
                <FloatingInput label="Household Monthly Income (₹)" type="number" value={formData.household_income || ''} onChange={(v) => update({ household_income: v, category_data: { ...formData.category_data, household_monthly_income: parseInt(v), monthly_income: parseInt(v) } })} />
                <FloatingInput label="Number of Dependents" type="number" value={formData.dependents || ''} onChange={(v) => update({ dependents: v, category_data: { ...formData.category_data, number_of_dependents: parseInt(v) } })} />
                <FloatingInput label="Household Monthly Expenses (₹)" type="number" value={formData.household_expenses || ''} onChange={(v) => update({ household_expenses: v, category_data: { ...formData.category_data, household_monthly_expenses: parseInt(v) } })} />
                <div className="p-3 bg-amber-50 border border-amber-200 rounded-input text-xs text-amber-700 font-body">
                  <AlertCircle size={14} className="inline mr-1" />
                  A nominee is mandatory for homemaker applications. Please complete Step 5.
                </div>
              </>
            )}
            {formData.user_category === 'daily_wage_worker' && (
              <>
                <FloatingInput label="Occupation Type" value={formData.occupation || ''} onChange={(v) => update({ occupation: v, category_data: { ...formData.category_data, occupation_type: v } })} />
                <FloatingInput label="Average Daily Earnings (₹)" type="number" value={formData.daily_earnings || ''} onChange={(v) => update({ daily_earnings: v, category_data: { ...formData.category_data, average_daily_earnings: parseInt(v), monthly_income: parseInt(v) * 22 } })} />
                <FloatingInput label="Days Worked per Month" type="number" value={formData.days_worked || ''} onChange={(v) => update({ days_worked: v, category_data: { ...formData.category_data, days_worked_per_month: parseInt(v) } })} />
              </>
            )}
            {/* Loan details for all categories */}
            <div className="pt-4 border-t border-user-border mt-6">
              <h3 className="text-lg font-display font-semibold text-user-text mb-4">Loan Request</h3>
              <FloatingInput label="Loan Amount (₹)" type="number" value={formData.loan_amount || ''} onChange={(v) => update({ loan_amount: v })} required />
              <div className="mt-4">
                <FloatingInput label="Tenure (months)" type="number" value={formData.loan_tenure || ''} onChange={(v) => update({ loan_tenure: v })} required />
              </div>
              <div className="mt-4">
                <FloatingInput label="Purpose of Loan" value={formData.loan_purpose || ''} onChange={(v) => update({ loan_purpose: v })} />
              </div>
            </div>
          </div>
        );

      case 3: // Documents
        return (
          <div className="space-y-4 max-w-lg mx-auto animate-fade-in">
            <h2 className="text-2xl font-display font-bold text-user-text mb-2">Upload Documents</h2>
            <p className="text-sm text-user-muted mb-6 font-body">Supporting documents strengthen your application. PDF, JPG, PNG — max 10MB each.</p>
            {[
              { type: 'identity', label: 'Identity Proof (Aadhaar/PAN)', required: false },
              ...(formData.user_category === 'farmer' ? [{ type: 'land_proof', label: 'Land Ownership Document', required: true }] : []),
              ...(formData.user_category === 'low_income_salaried' ? [{ type: 'salary_slip', label: 'Salary Slip', required: false }] : []),
              ...(formData.user_category === 'msme_owner' ? [{ type: 'bank_statement', label: 'Bank Statement', required: false }, { type: 'gst_certificate', label: 'GST Certificate', required: false }] : []),
              ...(formData.user_category === 'gig_worker' ? [{ type: 'platform_proof', label: 'Platform Registration Screenshot', required: false }] : []),
            ].map((doc) => (
              <div key={doc.type} className={`border-2 border-dashed rounded-card p-6 text-center transition-all ${uploadedDocs[doc.type] ? 'border-barclays-teal bg-risk-low_bg/30' : 'border-user-border hover:border-barclays-navy hover:bg-barclays-lightblue/20'}`}>
                {uploadedDocs[doc.type] ? (
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <CheckCircle size={20} className="text-barclays-teal" />
                      <div className="text-left">
                        <p className="text-sm font-medium text-user-text font-body">{uploadedDocs[doc.type].name}</p>
                        <p className="text-xs text-user-muted font-body">{(uploadedDocs[doc.type].size / 1024).toFixed(0)} KB</p>
                      </div>
                    </div>
                    <button onClick={() => { const docs = { ...uploadedDocs }; delete docs[doc.type]; setUploadedDocs(docs); }}
                      className="text-xs text-risk-very_high hover:underline font-body">Remove</button>
                  </div>
                ) : (
                  <label className="cursor-pointer block">
                    <Upload size={32} className="mx-auto text-user-muted mb-2" />
                    <p className="text-sm font-medium text-user-text font-body">{doc.label}</p>
                    <p className="text-xs text-user-muted mt-1 font-body">Drag & drop or tap to upload</p>
                    {doc.required && <span className="text-xs text-risk-very_high font-body">Required</span>}
                    <input type="file" className="hidden" accept=".pdf,.jpg,.jpeg,.png"
                      onChange={(e) => { if (e.target.files?.[0]) setUploadedDocs({ ...uploadedDocs, [doc.type]: e.target.files[0] }); }} />
                  </label>
                )}
              </div>
            ))}
          </div>
        );

      case 4: // Nominee
        return (
          <div className="space-y-4 max-w-lg mx-auto animate-fade-in">
            <h2 className="text-2xl font-display font-bold text-user-text mb-2">Nominee / Endorser</h2>
            <div className="p-4 bg-barclays-lightblue/50 rounded-card mb-6">
              <p className="text-sm text-barclays-navy font-body">
                Adding a nominee strengthens your application and can increase your eligible loan amount up to <strong>4x</strong>.
                {formData.user_category === 'homemaker' && <span className="text-risk-very_high font-semibold"> (Required for homemaker applications)</span>}
              </p>
            </div>
            <FloatingInput label="Nominee Full Name" value={formData.nominee_name || ''} onChange={(v) => update({ nominee_name: v })} />
            <div>
              <p className="text-xs text-user-muted mb-2 font-body">Relationship</p>
              <div className="flex flex-wrap gap-2">
                {['Spouse', 'Parent', 'Sibling', 'Employer', 'Community Leader'].map((r) => (
                  <button key={r} onClick={() => update({ nominee_relationship: r.toLowerCase() })}
                    className={`px-3 py-2 text-sm rounded-input border transition-all ${formData.nominee_relationship === r.toLowerCase() ? 'bg-barclays-navy text-white border-barclays-navy' : 'border-user-border text-user-muted'}`}>
                    {r}
                  </button>
                ))}
              </div>
            </div>
            <FloatingInput label="Nominee Phone" prefix="+91" value={formData.nominee_phone || ''} onChange={(v) => update({ nominee_phone: v })} />
            <FloatingInput label="Nominee Monthly Income (₹)" type="number" value={formData.nominee_income || ''} onChange={(v) => update({ nominee_income: v })} />
            <div>
              <p className="text-xs text-user-muted mb-2 font-body">Collateral Type</p>
              <div className="grid grid-cols-5 gap-2">
                {[
                  { id: 'property', label: '🏠 Property' }, { id: 'vehicle', label: '🚗 Vehicle' },
                  { id: 'gold', label: '💛 Gold' }, { id: 'fixed_deposit', label: '🏦 FD' }, { id: 'livestock', label: '🐄 Livestock' },
                ].map((c) => (
                  <button key={c.id} onClick={() => update({ collateral_type: c.id })}
                    className={`p-3 text-xs rounded-input border text-center transition-all ${formData.collateral_type === c.id ? 'bg-barclays-teal text-white border-barclays-teal' : 'border-user-border'}`}>
                    {c.label}
                  </button>
                ))}
              </div>
            </div>
            <FloatingInput label="Collateral Value (₹)" type="number" value={formData.collateral_value || ''} onChange={(v) => update({ collateral_value: v })} />
            {formData.nominee_name && formData.collateral_value && (
              <div className="p-4 bg-risk-low_bg rounded-card border border-risk-low/20 text-center animate-slide-up">
                <p className="text-sm text-user-muted font-body">With this nominee, your maximum eligible loan:</p>
                <p className="text-2xl font-display font-bold text-barclays-navy mt-1">
                  ₹{parseInt(formData.collateral_value) >= 100000 ? '5,00,000' : parseInt(formData.collateral_value) >= 50000 ? '1,00,000' : '50,000'}
                </p>
              </div>
            )}
          </div>
        );

      case 5: // Review
        return (
          <div className="max-w-lg mx-auto animate-fade-in">
            <h2 className="text-2xl font-display font-bold text-user-text mb-6">Review Your Application</h2>
            {[
              { title: 'Personal', step: 0, fields: [
                ['Name', formData.full_name], ['Phone', formData.phone_number], ['Email', formData.email],
              ]},
              { title: 'Category', step: 1, fields: [['Type', formData.user_category?.replace(/_/g, ' ')]] },
              { title: 'Loan Request', step: 2, fields: [
                ['Amount', `₹${parseInt(formData.loan_amount || '0').toLocaleString()}`],
                ['Tenure', `${formData.loan_tenure || '-'} months`],
              ]},
              ...(formData.nominee_name ? [{ title: 'Nominee', step: 4, fields: [
                ['Name', formData.nominee_name], ['Relationship', formData.nominee_relationship],
                ['Collateral', formData.collateral_type],
              ]}] : []),
            ].map((section) => (
              <div key={section.title} className="mb-4 p-4 bg-white rounded-card border border-user-border">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-sm font-semibold text-user-text font-body">{section.title}</h3>
                  <button onClick={() => dispatch(setStep(section.step))} className="text-xs text-barclays-blue hover:underline font-body">Edit</button>
                </div>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  {section.fields.filter(([_, v]) => v).map(([label, value]) => (
                    <div key={label as string}>
                      <span className="text-user-muted font-body">{label}: </span>
                      <span className="font-medium text-user-text font-body">{value as string}</span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-user-bg">
      {/* Top bar */}
      <header className="bg-white border-b border-user-border px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Shield size={20} className="text-barclays-gold" />
          <span className="font-display font-semibold text-barclays-navy">Credit Application</span>
        </div>
        <span className="text-xs text-user-muted font-body">Step {currentStep + 1} of {STEPS.length}</span>
      </header>

      {/* Step indicator */}
      <div className="bg-white border-b border-user-border px-6 py-4">
        <StepIndicator steps={STEPS} currentStep={currentStep} />
      </div>

      {/* Form content */}
      <main className="px-6 py-8 max-w-3xl mx-auto">
        {submitError && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-input text-sm text-red-600 font-body">
            {submitError}
          </div>
        )}
        {renderStep()}

        {/* Navigation buttons */}
        <div className="flex justify-between mt-8 max-w-lg mx-auto">
          {currentStep > 0 ? (
            <button onClick={prev} className="flex items-center gap-2 px-6 py-3 text-sm font-medium text-user-muted border border-user-border rounded-input hover:border-barclays-navy hover:text-barclays-navy transition-colors">
              <ArrowLeft size={16} /> Back
            </button>
          ) : <div />}

          {currentStep < STEPS.length - 1 ? (
            <button onClick={next}
              className="flex items-center gap-2 px-8 py-3 text-sm font-semibold bg-barclays-navy text-white rounded-input hover:bg-barclays-teal transition-colors disabled:opacity-50">
              Continue <ArrowRight size={16} />
            </button>
          ) : (
            <button onClick={handleSubmit} disabled={submitting}
              className="flex items-center gap-2 px-8 py-3 text-sm font-semibold bg-barclays-navy text-white rounded-input hover:bg-barclays-teal transition-colors disabled:opacity-60">
              {submitting ? <><Loader2 size={16} className="animate-spin" /> Processing...</> : <>Submit Application <ArrowRight size={16} /></>}
            </button>
          )}
        </div>
      </main>
    </div>
  );
};

export default ApplicationPage;
