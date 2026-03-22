import React from 'react';
import { Check } from 'lucide-react';

interface StepIndicatorProps {
  steps: string[];
  currentStep: number;
}

const StepIndicator: React.FC<StepIndicatorProps> = ({ steps, currentStep }) => {
  return (
    <div className="w-full">
      {/* Desktop: horizontal pills */}
      <div className="hidden md:flex items-center justify-center gap-0">
        {steps.map((label, index) => {
          const isCompleted = index < currentStep;
          const isActive = index === currentStep;
          const isUpcoming = index > currentStep;

          return (
            <React.Fragment key={label}>
              <div className="flex items-center gap-2">
                <div
                  className={`
                    w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold transition-all duration-300 ease-spring
                    ${isCompleted ? 'bg-barclays-teal text-white' : ''}
                    ${isActive ? 'bg-barclays-blue text-white shadow-score-glow scale-110' : ''}
                    ${isUpcoming ? 'bg-gray-100 text-gray-400 border-2 border-dashed border-gray-300' : ''}
                  `}
                >
                  {isCompleted ? <Check size={16} /> : index + 1}
                </div>
                <span
                  className={`
                    text-xs font-body whitespace-nowrap transition-colors duration-200
                    ${isActive ? 'text-barclays-navy font-semibold' : ''}
                    ${isCompleted ? 'text-barclays-teal' : ''}
                    ${isUpcoming ? 'text-gray-400' : ''}
                  `}
                >
                  {label}
                </span>
              </div>
              {index < steps.length - 1 && (
                <div
                  className={`
                    w-8 h-0.5 mx-1 transition-all duration-500
                    ${index < currentStep ? 'bg-barclays-teal' : 'bg-gray-200 border-t-2 border-dashed border-gray-300 h-0'}
                  `}
                />
              )}
            </React.Fragment>
          );
        })}
      </div>

      {/* Mobile: compact dots */}
      <div className="flex md:hidden items-center justify-center gap-2">
        {steps.map((_, index) => {
          const isCompleted = index < currentStep;
          const isActive = index === currentStep;
          return (
            <div
              key={index}
              className={`
                rounded-full transition-all duration-300
                ${isCompleted ? 'w-3 h-3 bg-barclays-teal' : ''}
                ${isActive ? 'w-6 h-3 bg-barclays-blue rounded-pill' : ''}
                ${!isCompleted && !isActive ? 'w-3 h-3 bg-gray-200' : ''}
              `}
            />
          );
        })}
      </div>
      <div className="md:hidden text-center mt-2">
        <span className="text-sm font-semibold text-barclays-navy">{steps[currentStep]}</span>
        <span className="text-xs text-user-muted ml-2">Step {currentStep + 1} of {steps.length}</span>
      </div>
    </div>
  );
};

export default StepIndicator;
